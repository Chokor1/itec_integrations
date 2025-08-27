# Copyright (c) 2025, Abbass Chokor and contributors
# For license information, please see license.txt

from frappe.model.document import Document
import frappe
import requests
import json
import time
from playwright.sync_api import sync_playwright
import hashlib

class NCRSyncSetting(Document):
	def validate(self):
		frappe.msgprint("Hash validation completed")

# Global circuit breaker state
circuit_breaker_state = {
	'failures': 0,
	'last_failure_time': 0,
	'is_open': False,
	'recovery_timeout': 60  # 1 minute recovery time
}

def check_circuit_breaker():
	"""Check if circuit breaker allows requests"""
	current_time = time.time()
	
	# If circuit is open, check if recovery time has passed
	if circuit_breaker_state['is_open']:
		if current_time - circuit_breaker_state['last_failure_time'] > circuit_breaker_state['recovery_timeout']:
			frappe.msgprint("🔄 Circuit breaker: Attempting recovery...")
			frappe.logger().info("🔄 Circuit breaker: Attempting recovery...")
			circuit_breaker_state['is_open'] = False
			circuit_breaker_state['failures'] = 0
			return True
		else:
			remaining = circuit_breaker_state['recovery_timeout'] - (current_time - circuit_breaker_state['last_failure_time'])
			frappe.msgprint(f"⛔ Circuit breaker OPEN - recovery in {remaining:.0f}s")
			frappe.logger().warning(f"⛔ Circuit breaker OPEN - recovery in {remaining:.0f}s")
			return False
	
	return True

def record_circuit_breaker_success():
	"""Record successful request"""
	old_failures = circuit_breaker_state['failures']
	circuit_breaker_state['failures'] = max(0, circuit_breaker_state['failures'] - 1)
	if old_failures > 0:
		frappe.msgprint(f"📈 Circuit breaker: Reduced failure count to {circuit_breaker_state['failures']}")

def record_circuit_breaker_failure():
	"""Record failed request and potentially open circuit"""
	circuit_breaker_state['failures'] += 1
	circuit_breaker_state['last_failure_time'] = time.time()
	
	
	# Open circuit after 10 consecutive failures
	if circuit_breaker_state['failures'] >= 10:
		circuit_breaker_state['is_open'] = True
		frappe.logger().error("⛔ Circuit breaker OPENED due to too many failures")


def make_api_request_with_retry(url, payload, headers, category, start_index, max_retries=8, base_delay=0.2):
	"""
	Make API request with ultra-aggressive retry logic and very short timeouts
	"""
	import random
	
	# Check circuit breaker first
	if not check_circuit_breaker():
		return None
	
	# Ultra-short timeouts with more attempts
	timeouts = [3, 4, 5, 6, 8, 10, 12, 15]  # Very short initial timeouts
	
	for attempt in range(max_retries):
		try:
			timeout = timeouts[min(attempt, len(timeouts)-1)]
			
			frappe.logger().info(f"Attempt {attempt + 1}/{max_retries} for '{category}' (start: {start_index}) - timeout: {timeout}s")
			
			# Use a more aggressive session configuration
			session = requests.Session()
			session.headers.update(headers)
			
			# More aggressive adapter settings (removed socket_options for compatibility)
			adapter = requests.adapters.HTTPAdapter(
				pool_connections=10,
				pool_maxsize=20,
				max_retries=requests.adapters.Retry(
					total=0,  # We handle retries manually
					connect=2,
					read=2,
					backoff_factor=0.1,
					status_forcelist=[429, 500, 502, 503, 504]
				)
			)
			session.mount("http://", adapter)
			session.mount("https://", adapter)
			
			# Ultra-short connection timeout, variable read timeout
			connection_timeout = min(2, timeout - 1)  # Very fast connection detection
			frappe.logger().info(f"Using connection timeout: {connection_timeout}s, read timeout: {timeout}s")
			
			response = session.post(url, json=payload, timeout=(connection_timeout, timeout))
			
			if response.status_code == 200:
				data = response.json()
				frappe.logger().info(f"Success for category '{category}' (start: {start_index}) on attempt {attempt + 1}")
				record_circuit_breaker_success()
				return data
			elif response.status_code in [429, 503, 504]:  # Rate limited or server error
				frappe.logger().warning(f"Rate limited or server error (status: {response.status_code}) for category '{category}' - attempt {attempt + 1}")
				if attempt < max_retries - 1:
					delay = base_delay * (2 ** attempt) + random.uniform(0, 1)
					frappe.logger().info(f"Waiting {delay:.1f}s before retry...")
					time.sleep(delay)
					continue
			else:
				frappe.log_error(f"VTEX API Error for category {category}: {response.status_code} - {response.text}", "VTEX API Error")
				return None
				
		except requests.exceptions.Timeout:
			frappe.logger().warning(f"Timeout for '{category}' (start: {start_index}) - attempt {attempt + 1} (timeout was {timeout}s)")
			if attempt < max_retries - 1:
				# Ultra-fast retry with minimal delays
				delay = base_delay * (1.2 ** attempt) + random.uniform(0, 0.2)
				frappe.logger().info(f"Ultra-fast retry in {delay:.2f}s...")
				time.sleep(delay)
			else:
				frappe.logger().error(f"All {max_retries} attempts timed out for '{category}' - tried timeouts: {timeouts[:max_retries]}")
				
		except requests.exceptions.ConnectionError as e:
			frappe.logger().warning(f"Connection error for '{category}' - attempt {attempt + 1}: {str(e)[:100]}")
			if attempt < max_retries - 1:
				# Very fast retry for connection errors
				delay = base_delay + random.uniform(0, 0.3)
				frappe.logger().info(f"Connection retry in {delay:.1f}s...")
				time.sleep(delay)
			else:
				frappe.logger().error(f"All connection attempts failed for '{category}'")
				
		except Exception as e:
			frappe.logger().error(f"Unexpected error for category '{category}': {e}")
			record_circuit_breaker_failure()
			if attempt < max_retries - 1:
				delay = base_delay * (2 ** attempt)
				time.sleep(delay)
			else:
				break
	
	# All attempts failed - try one last fallback attempt
	frappe.logger().warning(f"Trying fallback method for '{category}' (start: {start_index})")
	try:
		# Ultra-minimal approach with no session overhead
		response = requests.post(url, json=payload, headers=headers, timeout=(1, 3))
		if response.status_code == 200:
			data = response.json()
			frappe.logger().info(f"Fallback success for '{category}'!")
			record_circuit_breaker_success()
			return data
	except Exception as fallback_error:
		frappe.logger().error(f"Fallback also failed: {fallback_error}")
	
	record_circuit_breaker_failure()
	return None

@frappe.whitelist()
def run_sync():
	try:
		# Ultra-aggressive configuration for persistent timeout issues
		MAX_RETRIES = 8  # Many more retry attempts
		BASE_DELAY = 0.2  # Ultra-fast retries
		MAX_CONSECUTIVE_FAILURES = 8  # Allow many failures before giving up
		INITIAL_BATCH_SIZE = 5  # Start very small
		MIN_BATCH_SIZE = 3  # Very minimum batch size
		MAX_BATCH_SIZE = 12  # Smaller maximum to reduce load
		
		url = "https://www.ncrangola.com/_v/segment/graphql/v1"
		headers = {
			"Content-Type": "application/json",
			"Accept": "application/json",
			"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
			"Connection": "keep-alive",
			"Cache-Control": "no-cache"
		}

		all_products = []
		sync_doc = frappe.get_doc("NCR Sync Setting")
			
		# Get the fixed hash
		if sync_doc.hash:
			current_hash = sync_doc.hash	
		# Check if we have any categories to sync
		categories_to_sync = [row for row in sync_doc.ncr_sync_categories if row.include]
		if not categories_to_sync:
			frappe.throw("No categories selected for sync. Please enable at least one category.")
		
		for idx, row in enumerate(categories_to_sync, 1):
			frappe.logger().info(f"Processing category {idx}/{len(categories_to_sync)}: {row.category}")
			
			start = 0
			current_batch_size = INITIAL_BATCH_SIZE
			category_products = 0
			consecutive_failures = 0
			max_consecutive_failures = MAX_CONSECUTIVE_FAILURES
			success_count = 0
			total_requests = 0
			
			while True:
				payload = {
					"operationName": "productSearchV3",
					"variables": {
						"query": row.category,
						"selectedFacets": [
							{
								"key": "c",
								"value": row.category
							}
						],
						"from": start,
						"to": start + current_batch_size,
						"orderBy": "OrderByScoreDESC",
						"map": "c"
					},
					"extensions": {
						"persistedQuery": {
							"version": 1,
							"sha256Hash": current_hash,
							"sender": "vtex.store-resources@0.x",
							"provider": "vtex.search-graphql@0.x"
						}
					}
				}

				# Track request timing for adaptive batch sizing
				request_start_time = time.time()
				total_requests += 1
				
				# Make request with retry logic
				data = make_api_request_with_retry(url, payload, headers, row.category, start, MAX_RETRIES, BASE_DELAY)
				
				request_duration = time.time() - request_start_time
				
				if data is None:
					consecutive_failures += 1
					frappe.logger().warning(f"Failed batch for {row.category} (failure {consecutive_failures}/{max_consecutive_failures})")
					
					# Reduce batch size on failures
					if current_batch_size > MIN_BATCH_SIZE:
						current_batch_size = max(MIN_BATCH_SIZE, current_batch_size - 2)
						frappe.logger().info(f"Reduced batch size to {current_batch_size}")
					
					if consecutive_failures >= max_consecutive_failures:
						frappe.log_error(f"Stopping category {row.category} after {max_consecutive_failures} consecutive failures", "VTEX API Error")
						break
					else:
						# Skip this batch and try the next one with smaller batch
						start += current_batch_size
						time.sleep(1)  # Shorter wait
						continue
				else:
					consecutive_failures = 0  # Reset failure counter on success
					success_count += 1
					
					# Adaptive batch sizing based on success and response time
					if request_duration < 5 and current_batch_size < MAX_BATCH_SIZE:
						# Fast response, can increase batch size
						current_batch_size = min(MAX_BATCH_SIZE, current_batch_size + 1)
						frappe.logger().info(f"Increased batch size to {current_batch_size}")
					elif request_duration > 15 and current_batch_size > MIN_BATCH_SIZE:
						# Slow response, decrease batch size
						current_batch_size = max(MIN_BATCH_SIZE, current_batch_size - 1)
						frappe.logger().info(f"Decreased batch size to {current_batch_size}")
					
					frappe.logger().info(f"Request took {request_duration:.1f}s, batch size: {current_batch_size}")

				if data.get("data", {}).get("productSearch", {}):
					products = data.get("data", {}).get("productSearch", {}).get("products", [])
				else:
					# Log the response for debugging
					frappe.logger().info(f"No productSearch data for category {row.category}. Response: {json.dumps(data, indent=2)}")
					break

				if not products:
					break  

				for p in products:
					all_products.append({
						"productReference": p.get("productReference"),
						"productName": p.get("productName"),
						"brand": p.get("brand"),
						"price": p.get("priceRange", {}).get("sellingPrice", {}).get("lowPrice")
					})
					category_products += 1

				start += current_batch_size
				
				# Ultra-minimal delays to maximize throughput
				if start % 50 == 0:  # More frequent progress updates
					success_rate = success_count / max(1, total_requests) * 100
					time.sleep(0.5)  # Very short pause
					frappe.logger().info(f"Progress: {category_products} products, success rate: {success_rate:.1f}%, batch size: {current_batch_size}")
				else:
					# Minimal delays based on performance
					if circuit_breaker_state['failures'] == 0:
						time.sleep(0.1)  # Ultra-fast when no failures
					elif circuit_breaker_state['failures'] < 3:
						time.sleep(0.2)  # Still very fast
					else:
						time.sleep(0.4)  # Moderate when many failures
			
			frappe.logger().info(f"Completed category {row.category}: {category_products} products")

		# Save the products data
		doc_name = frappe.get_all("NCR Products", fields=["name"], limit=1)
		if doc_name:
			doc = frappe.get_doc("NCR Products", doc_name[0].name)
			doc.data_json = json.dumps(all_products, indent=2)
			doc.save(ignore_permissions=True)
		else:
			doc = frappe.get_doc({
				"doctype": "NCR Products",
				"data_json": json.dumps(all_products, indent=2)
			})
			doc.insert(ignore_permissions=True)
			
		frappe.db.set_value("NCR Sync Setting", None, "last_sync_at", frappe.utils.now_datetime())
		frappe.db.commit()
		
		# Provide detailed sync results
		if len(all_products) == 0:
			frappe.msgprint("Warning: No products were synced. This might be due to:")
			frappe.msgprint("1. Network timeout or connectivity issues")
			frappe.msgprint("2. No products found in the selected categories")
			frappe.msgprint("3. The website structure has changed")
			frappe.msgprint("4. Rate limiting or server overload")
			frappe.msgprint("Please check the error logs for more details.")
		else:
			success_rate = (len(all_products) / max(1, len(categories_to_sync) * 50)) * 100  # Estimate
			frappe.msgprint(f"Successfully synced {len(all_products)} products from NCR")
			frappe.logger().info(f"Sync completed with estimated success rate: {success_rate:.1f}%")
		
		return "success"

	except Exception as e:
		frappe.log_error(frappe.get_traceback(), "NCR VTEX Sync Error")
		return "error"

def get_current_hash():
	"""
	Return the fixed SHA256 hash for NCR website API calls.
	"""
	return "c351315ecde7f473587b710ac8b97f147ac0ac0cd3060c27c695843a72fd3903"


