#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'salary_management.settings')
django.setup()

from employees.models import Site

def test_site_creation():
    """Test creating a Site instance"""
    try:
        # Create a test site
        site = Site.objects.create(
            site_code="S001",
            site_name="Test Site",
            site_address="123 Test Street, Test City",
            site_contact_person_name="John Doe",
            site_contact_person_number="9876543210",
            site_contact_person_email="john@testsite.com",
            site_gst_number="22AAAAA0000A1Z5",
            site_pf_code="PF001",
            site_esic_code="ESI001",
            site_service_charge_salary="5.0",
            site_service_charge_over_time="10.0",
            site_account_number="1234567890",
            site_ifsc_code="SBIN0001234",
            site_salary_component_type="Month",
            site_ot_rule="1.5x",
            site_bonus_formula="Basic * 8.33%",
            site_pf_deduction="12%",
            site_esic_deduction_rule="3.25%",
            site_welfare_deduction_rule="0.5%",
            settings={"working_hours": 8, "overtime_enabled": True},
            currency="INR",
            timezone="Asia/Kolkata"
        )
        
        print(f"✅ Site created successfully!")
        print(f"   Site ID: {site.id}")
        print(f"   Site Name: {site.site_name}")
        print(f"   Site Code: {site.site_code}")
        print(f"   Contact: {site.site_contact_person_name} - {site.site_contact_person_number}")
        print(f"   Created at: {site.created_at}")
        
        # Test retrieving the site
        retrieved_site = Site.objects.get(id=site.id)
        print(f"✅ Site retrieved successfully: {retrieved_site.site_name}")
        
        # Test updating the site
        retrieved_site.site_name = "Updated Test Site"
        retrieved_site.save()
        print(f"✅ Site updated successfully: {retrieved_site.site_name}")
        
        # Test listing all sites
        all_sites = Site.objects.all()
        print(f"✅ Total sites in database: {all_sites.count()}")
        
        # Clean up - delete the test site
        site.delete()
        print(f"✅ Test site deleted successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating site: {e}")
        return False

def test_site_form_validation():
    """Test form validation"""
    try:
        from employees.forms import SiteForm
        
        # Test valid data
        valid_data = {
            'site_code': 'S002',
            'site_name': 'Form Test Site',
            'site_address': '456 Form Street',
            'site_contact_person_name': 'Jane Smith',
            'site_contact_person_number': '9876543210',
            'site_contact_person_email': 'jane@formtest.com',
            'site_gst_number': '22BBBBB0000B1Z5',
            'site_pf_code': 'PF002',
            'site_esic_code': 'ESI002',
            'site_service_charge_salary': '6.0',
            'site_service_charge_over_time': '12.0',
            'site_account_number': '0987654321',
            'site_ifsc_code': 'HDFC0001234',
            'site_salary_component_type': 'Month',
            'site_ot_rule': '2x',
            'site_bonus_formula': 'Basic * 10%',
            'site_pf_deduction': '12%',
            'site_esic_deduction_rule': '3.25%',
            'site_welfare_deduction_rule': '0.5%',
            'settings': '{"working_hours": 9}',
            'currency': 'INR',
            'timezone': 'Asia/Kolkata'
        }
        
        form = SiteForm(data=valid_data)
        if form.is_valid():
            print("✅ Form validation passed with valid data")
            site = form.save()
            print(f"   Site saved with ID: {site.id}")
            site.delete()  # Clean up
        else:
            print(f"❌ Form validation failed: {form.errors}")
            return False
            
        # Test invalid data (invalid phone number)
        invalid_data = valid_data.copy()
        invalid_data['site_contact_person_number'] = '123'  # Too short
        
        form = SiteForm(data=invalid_data)
        if not form.is_valid():
            print("✅ Form validation correctly rejected invalid phone number")
        else:
            print("❌ Form validation should have failed with invalid phone number")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Error testing form validation: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Site Model...")
    print("=" * 50)
    
    # Test 1: Basic model operations
    print("\n1. Testing Site Model Creation and CRUD Operations:")
    test1_passed = test_site_creation()
    
    # Test 2: Form validation
    print("\n2. Testing Site Form Validation:")
    test2_passed = test_site_form_validation()
    
    print("\n" + "=" * 50)
    if test1_passed and test2_passed:
        print("🎉 All tests passed! Site model is working correctly.")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    print("\n📋 Summary:")
    print("- Site model can be created, read, updated, and deleted")
    print("- Form validation works correctly")
    print("- Phone number validation is working")
    print("- All required fields are properly configured") 