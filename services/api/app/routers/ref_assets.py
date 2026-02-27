from fastapi import APIRouter

router = APIRouter()


@router.get('/v2/ref/assets')
def get_assets_ref():
    mac_types = [
        {'key': 'MAC_PHONE_BANK', 'label': 'Phone Bank'},
        {'key': 'MAC_EVENT_SUPPORT', 'label': 'Event Support'},
        {'key': 'MAC_SCHOOL_VISIT', 'label': 'School Visit'},
        {'key': 'MAC_LEAD_FOLLOWUP', 'label': 'Lead Followup'},
        {'key': 'MAC_PROCESSING_SUPPORT', 'label': 'Processing Support'},
        {'key': 'MAC_SOCIAL_MEDIA_ENGAGEMENT', 'label': 'Social Media Engagement'},
        {'key': 'MAC_ADMIN_SUPPORT', 'label': 'Admin Support'},
        {'key': 'MAC_RECRUITING_STATION_SUPPORT', 'label': 'Recruiting Station Support'},
    ]

    tair_types = [
        {'key': 'TAIR_SCHOOL_RECRUITING', 'label': 'School Recruiting'},
        {'key': 'TAIR_COMMUNITY_EVENT', 'label': 'Community Event'},
        {'key': 'TAIR_SPORTING_EVENT', 'label': 'Sporting Event'},
        {'key': 'TAIR_DIGITAL_CAMPAIGN', 'label': 'Digital Campaign'},
        {'key': 'TAIR_TRADITIONAL_MEDIA', 'label': 'Traditional Media'},
        {'key': 'TAIR_PARTNERSHIP_SPONSORSHIP', 'label': 'Partnership / Sponsorship'},
        {'key': 'TAIR_STATION_BRANDING', 'label': 'Station Branding'},
        {'key': 'TAIR_EDUCATION_SUPPORT', 'label': 'Education Support'},
    ]

    meb_items = [
        {'key': 'MEB_EVENT_SUPPORT', 'label': 'Event Support'},
        {'key': 'MEB_LOCAL_ADVERTISING', 'label': 'Local Advertising'},
        {'key': 'MEB_STATION_BRANDING', 'label': 'Station Branding'},
        {'key': 'MEB_EDUCATION_CONVENTION_SUPPORT', 'label': 'Education / Convention Support'},
        {'key': 'MEB_NATIONAL_EVENT_SUPPORT', 'label': 'National Event Support'},
        {'key': 'MEB_ASB_ASSET_SUPPORT', 'label': 'ASB Asset Support'},
        {'key': 'MEB_TRAVEL_MISC', 'label': 'Travel / Misc'},
        {'key': 'MEB_PRINT_COLLATERAL', 'label': 'Print Collateral'},
        {'key': 'MEB_DIGITAL_MEDIA_BUY', 'label': 'Digital Media Buy'},
    ]

    return {
        'mac_types': mac_types,
        'tair_types': tair_types,
        'meb_items': meb_items,
    }
