# NCR Angola Integration

This module provides integration with the NCR Angola website (https://www.ncrangola.com/) to scrape product information and sync it with your ERPNext system.

## Features

- **Dynamic Hash Extraction**: Automatically extracts the current SHA256 hash from the NCR website to avoid "PersistedQueryNotFound" errors
- **Product Synchronization**: Syncs products from multiple categories
- **Fallback Mechanism**: Uses a known working hash if dynamic extraction fails
- **Rate Limiting**: Includes delays to avoid being blocked by the website
- **Error Handling**: Comprehensive error handling and logging

## Recent Updates

### Hash Management Fix
The integration has been updated with a robust hash management system that combines validation with dynamic extraction. This resolves the "PersistedQueryNotFound" error that was occurring due to website changes.

### Key Improvements
1. **Hash Validation**: Tests if the current hash is still valid before using it
2. **Smart Fallback**: Uses a known working hash as primary method with dynamic extraction as backup
3. **API Testing**: Validates hashes by making actual API calls to ensure they work
4. **Better Error Handling**: More detailed error messages and debugging information
5. **Reliable Operation**: Prioritizes stability over dynamic extraction

## Installation

1. Install the required dependencies:
```bash
pip install playwright requests beautifulsoup4
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

3. Install the app in your Frappe bench:
```bash
bench get-app itec_integrations
bench install-app itec_integrations
```

## Configuration

1. Go to **NCR Sync Setting** in your Frappe desk
2. Add categories you want to sync (e.g., "informatica", "escritorio", etc.)
3. Enable the categories you want to sync by checking the "Include" checkbox
4. Save the settings

## Usage

### Manual Sync
1. Navigate to **NCR Sync Setting**
2. Click the "Run Sync" button
3. Monitor the progress and check the results

### Automated Sync
You can set up a scheduled task to run the sync automatically:

```python
# In a custom app or script
from itec_integrations.doctype.ncr_sync_setting.ncr_sync_setting import run_sync

# Run the sync
result = run_sync()
```

## Troubleshooting

### No Products Synced (0 products)
If you get 0 products synced, check the following:

1. **Categories**: Ensure you have categories configured and enabled in NCR Sync Setting
2. **Network**: Check if the website is accessible from your server
3. **Hash Issues**: The system will automatically use a fallback hash if extraction fails
4. **Logs**: Check the error logs for detailed information

### Hash Extraction Issues
If hash extraction fails:

1. The system will automatically use a known working hash
2. Check the logs for extraction errors
3. Ensure Playwright is properly installed
4. Verify network connectivity to ncrangola.com

### API Errors
If you get API errors:

1. Check the response in the error logs
2. The hash might need to be updated manually
3. The website structure might have changed

## Technical Details

### Hash Management Process
1. **Validation First**: Tests if the known working hash is still valid using API calls
2. **Primary Method**: Uses the validated hash if it works
3. **Fallback Extraction**: If validation fails, attempts dynamic extraction using Playwright
4. **Hash Testing**: Tests any extracted hashes by making actual productSearchV3 API calls
5. **Graceful Degradation**: Returns known hash as last resort if all else fails

### API Endpoint
- **URL**: `https://www.ncrangola.com/_v/segment/graphql/v1`
- **Method**: POST
- **Operation**: `productSearchV3`

### Data Structure
Products are stored with the following structure:
```json
{
  "productReference": "string",
  "productName": "string", 
  "brand": "string",
  "price": "number"
}
```

## Testing

### Test Hash Extraction
```bash
cd apps/itec_integrations
python test_ncr_hash.py
```

### Test API Calls
```bash
cd apps/itec_integrations
python test_ncr_api.py
```

### Test Sync Function
```bash
cd apps/itec_integrations
python test_sync_function.py
```

## Dependencies

- `playwright==1.48.0`: For browser automation and request interception
- `requests>=2.25.1`: For HTTP requests
- `beautifulsoup4>=4.9.3`: For HTML parsing (if needed)

## Security Notes

- The integration uses a headless browser for hash extraction
- No sensitive data is stored or transmitted
- All requests use standard HTTP headers
- Rate limiting is implemented to avoid overwhelming the target website

## Support

If you encounter issues:

1. Check the error logs in Frappe
2. Run the test scripts to verify functionality
3. Ensure all dependencies are properly installed
4. Verify network connectivity to the target website

## Changelog

### Version 2.0
- Added dynamic hash extraction
- Improved error handling
- Added fallback hash mechanism
- Enhanced logging and debugging
- Better rate limiting

### Version 1.0
- Initial implementation with hardcoded hash
- Basic product synchronization
- Simple error handling
