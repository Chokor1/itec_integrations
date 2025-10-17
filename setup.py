from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in itec_integrations/__init__.py
from itec_integrations import __version__ as version

setup(
	name="itec_integrations",
	version=version,
	description="Itec Integrations is a custom Frappe application developed for Itec, designed to centralize and manage system integrations with commercial partners. This app enables seamless synchronization of stock, pricing, and product information between Itec and third-party platforms such as suppliers, resellers, and logistic partners.",
	author="Abbass Chokor",
	author_email="abbasschokor225@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
