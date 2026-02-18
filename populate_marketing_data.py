#!/usr/bin/env python3
"""
Populate sample marketing engagement data from various platforms.
Simulates data from: Vantage, Sprinkler, EMM, MACs, Social Media, etc.
"""

import sqlite3
import os
import random
from datetime import datetime, timedelta

DB_FILE = os.path.join(os.path.dirname(__file__), "recruiting.db")


def populate():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    now = datetime.now()
    
    print("Populating sample marketing engagement data...")

    # Create sample campaigns
    campaigns = [
        ('CAMP-FB-001', 'Army Strong Social Campaign', 'social_media', 'Facebook', (now - timedelta(days=60)).strftime('%Y-%m-%d'), (now + timedelta(days=30)).strftime('%Y-%m-%d'), 'active', '18-24 Males', 15000, 12500, 'brand_awareness'),
        ('CAMP-IG-001', 'Be All You Can Be Instagram', 'social_media', 'Instagram', (now - timedelta(days=45)).strftime('%Y-%m-%d'), (now + timedelta(days=45)).strftime('%Y-%m-%d'), 'active', '18-24 Females', 12000, 10200, 'engagement'),
        ('CAMP-VAN-001', 'Vantage Display Network Q1', 'digital_advertising', 'Vantage', (now - timedelta(days=90)).strftime('%Y-%m-%d'), (now - timedelta(days=1)).strftime('%Y-%m-%d'), 'completed', '18-35 All', 50000, 48900, 'lead_generation'),
        ('CAMP-EMAIL-001', 'MACs Recruiter Outreach', 'email_marketing', 'MACs', (now - timedelta(days=30)).strftime('%Y-%m-%d'), (now + timedelta(days=30)).strftime('%Y-%m-%d'), 'active', 'High School Seniors', 5000, 3200, 'conversion'),
        ('CAMP-YT-001', 'YouTube Recruitment Stories', 'video_marketing', 'YouTube', (now - timedelta(days=75)).strftime('%Y-%m-%d'), (now + timedelta(days=15)).strftime('%Y-%m-%d'), 'active', '16-24 All', 25000, 22100, 'awareness'),
        ('CAMP-LI-001', 'LinkedIn Officer Recruitment', 'social_media', 'LinkedIn', (now - timedelta(days=40)).strftime('%Y-%m-%d'), (now + timedelta(days=50)).strftime('%Y-%m-%d'), 'active', 'College Graduates', 8000, 6900, 'lead_generation'),
        ('CAMP-TT-001', 'TikTok Challenge - Service Life', 'social_media', 'TikTok', (now - timedelta(days=20)).strftime('%Y-%m-%d'), (now + timedelta(days=40)).strftime('%Y-%m-%d'), 'active', '16-22 All', 10000, 7500, 'viral_engagement'),
        ('CAMP-SPR-001', 'Sprinkler Email Nurture Series', 'email_marketing', 'Sprinkler', (now - timedelta(days=50)).strftime('%Y-%m-%d'), (now + timedelta(days=10)).strftime('%Y-%m-%d'), 'active', 'Warm Leads', 7000, 5800, 'conversion'),
    ]

    for camp in campaigns:
        cursor.execute("""
        INSERT OR REPLACE INTO marketing_campaigns 
        (campaign_id, campaign_name, campaign_type, platform, start_date, end_date, status, target_audience, budget_allocated, budget_spent, objective, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, camp + (now.isoformat(), now.isoformat()))

    print(f"✅ Created {len(campaigns)} marketing campaigns")

    # Generate daily engagement metrics for each campaign
    metrics_count = 0
    platforms_metrics = {
        'Facebook': {'base_impressions': 50000, 'base_engagement_rate': 0.035},
        'Instagram': {'base_impressions': 45000, 'base_engagement_rate': 0.042},
        'Vantage': {'base_impressions': 100000, 'base_engagement_rate': 0.008},
        'MACs': {'base_impressions': 5000, 'base_engagement_rate': 0.22},
        'YouTube': {'base_impressions': 75000, 'base_engagement_rate': 0.015},
        'LinkedIn': {'base_impressions': 15000, 'base_engagement_rate': 0.028},
        'TikTok': {'base_impressions': 120000, 'base_engagement_rate': 0.065},
        'Sprinkler': {'base_impressions': 8000, 'base_engagement_rate': 0.19},
    }

    for camp in campaigns:
        campaign_id, campaign_name, campaign_type, platform, start_date, end_date, status, target, budget_a, budget_s, obj = camp
        
        # Generate metrics for last 30 days
        for days_ago in range(30, 0, -1):
            metric_date = (now - timedelta(days=days_ago)).strftime('%Y-%m-%d')
            
            base = platforms_metrics.get(platform, {'base_impressions': 10000, 'base_engagement_rate': 0.02})
            
            impressions = int(base['base_impressions'] * random.uniform(0.7, 1.3))
            views = int(impressions * random.uniform(0.4, 0.9))
            reach = int(impressions * random.uniform(0.5, 0.8))
            engagement_rate = base['base_engagement_rate'] * random.uniform(0.8, 1.2)
            engagements = int(impressions * engagement_rate)
            clicks = int(engagements * random.uniform(0.15, 0.35))
            shares = int(engagements * random.uniform(0.05, 0.15))
            likes = int(engagements * random.uniform(0.6, 0.8))
            comments = int(engagements * random.uniform(0.05, 0.12))
            saves = int(engagements * random.uniform(0.03, 0.08))
            video_views = int(views * random.uniform(0.3, 0.7)) if platform in ['YouTube', 'TikTok', 'Facebook', 'Instagram'] else 0
            video_completion = random.uniform(0.35, 0.75) if video_views > 0 else 0
            ctr = (clicks / impressions * 100) if impressions > 0 else 0
            conversions = int(clicks * random.uniform(0.05, 0.15))
            conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
            cost_per_impression = (budget_s / 30) / impressions if impressions > 0 else 0
            cost_per_click = (budget_s / 30) / clicks if clicks > 0 else 0
            cost_per_engagement = (budget_s / 30) / engagements if engagements > 0 else 0
            
            cursor.execute("""
            INSERT OR REPLACE INTO marketing_engagement_metrics 
            (campaign_id, platform, metric_date, impressions, views, reach, engagements, clicks, shares, likes, comments, saves, 
             video_views, video_completion_rate, click_through_rate, engagement_rate, cost_per_impression, cost_per_click, 
             cost_per_engagement, conversions, conversion_rate, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (campaign_id, platform, metric_date, impressions, views, reach, engagements, clicks, shares, likes, comments, saves,
                  video_views, round(video_completion, 3), round(ctr, 3), round(engagement_rate * 100, 3), round(cost_per_impression, 4),
                  round(cost_per_click, 2), round(cost_per_engagement, 2), conversions, round(conversion_rate, 2), now.isoformat()))
            metrics_count += 1

    print(f"✅ Created {metrics_count} daily engagement metrics")

    # Generate sample social media posts
    social_platforms = ['Facebook', 'Instagram', 'Twitter/X', 'LinkedIn', 'TikTok', 'YouTube']
    post_types = ['image', 'video', 'carousel', 'story', 'reel', 'short']
    posts_count = 0
    
    for i in range(100):
        platform = random.choice(social_platforms)
        post_type = random.choice(post_types)
        posted_date = (now - timedelta(days=random.randint(1, 60))).strftime('%Y-%m-%d %H:%M:%S')
        
        # Link some posts to campaigns
        campaign_id = campaigns[random.randint(0, len(campaigns)-1)][0] if random.random() > 0.3 else None
        
        impressions = random.randint(5000, 200000)
        views = int(impressions * random.uniform(0.3, 0.8))
        reach = int(impressions * random.uniform(0.5, 0.7))
        engagements = int(impressions * random.uniform(0.01, 0.08))
        clicks = int(engagements * random.uniform(0.1, 0.3))
        shares = int(engagements * random.uniform(0.05, 0.15))
        likes = int(engagements * random.uniform(0.6, 0.8))
        comments = int(engagements * random.uniform(0.05, 0.12))
        saves = int(engagements * random.uniform(0.03, 0.08))
        engagement_rate = (engagements / impressions * 100) if impressions > 0 else 0
        
        cursor.execute("""
        INSERT INTO social_media_posts 
        (post_id, campaign_id, platform, post_type, content, posted_date, impressions, views, engagements, clicks, shares, 
         likes, comments, saves, reach, engagement_rate, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (f"POST-{platform[:2].upper()}-{i:04d}", campaign_id, platform, post_type, f"Sample {post_type} post about Army recruitment", 
              posted_date, impressions, views, engagements, clicks, shares, likes, comments, saves, reach, round(engagement_rate, 2),
              now.isoformat(), now.isoformat()))
        posts_count += 1

    print(f"✅ Created {posts_count} social media posts")

    # Generate email marketing data
    email_platforms = ['MACs', 'Sprinkler']
    emails_count = 0
    
    for i in range(50):
        platform = random.choice(email_platforms)
        send_date = (now - timedelta(days=random.randint(1, 90))).strftime('%Y-%m-%d')
        campaign_id = campaigns[3][0] if platform == 'MACs' else campaigns[7][0]  # Link to email campaigns
        
        recipients = random.randint(500, 10000)
        delivered = int(recipients * random.uniform(0.95, 0.99))
        opened = int(delivered * random.uniform(0.15, 0.35))
        clicked = int(opened * random.uniform(0.15, 0.30))
        bounced = recipients - delivered
        unsubscribed = int(delivered * random.uniform(0.001, 0.005))
        conversions = int(clicked * random.uniform(0.05, 0.20))
        
        open_rate = (opened / delivered * 100) if delivered > 0 else 0
        click_rate = (clicked / delivered * 100) if delivered > 0 else 0
        click_to_open = (clicked / opened * 100) if opened > 0 else 0
        bounce_rate = (bounced / recipients * 100) if recipients > 0 else 0
        conversion_rate = (conversions / clicked * 100) if clicked > 0 else 0
        
        cursor.execute("""
        INSERT INTO email_marketing_metrics 
        (email_id, campaign_id, platform, email_subject, send_date, recipients, delivered, opened, clicked, bounced, 
         unsubscribed, conversions, open_rate, click_rate, click_to_open_rate, bounce_rate, conversion_rate, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (f"EMAIL-{platform[:3].upper()}-{i:04d}", campaign_id, platform, f"Join the Army - {random.choice(['Benefits', 'Training', 'Career', 'Education', 'Leadership'])} Edition",
              send_date, recipients, delivered, opened, clicked, bounced, unsubscribed, conversions,
              round(open_rate, 2), round(click_rate, 2), round(click_to_open, 2), round(bounce_rate, 2), round(conversion_rate, 2),
              now.isoformat(), now.isoformat()))
        emails_count += 1

    print(f"✅ Created {emails_count} email marketing records")

    # Generate digital advertising data
    ad_platforms = ['Vantage', 'Google Ads', 'Display Network', 'Facebook', 'Instagram']
    ads_count = 0
    
    for i in range(75):
        platform = random.choice(ad_platforms)
        ad_type = random.choice(['display', 'video', 'carousel', 'story', 'search', 'native'])
        start_date = (now - timedelta(days=random.randint(30, 90))).strftime('%Y-%m-%d')
        end_date = (now + timedelta(days=random.randint(-10, 30))).strftime('%Y-%m-%d')
        campaign_id = campaigns[2][0] if platform == 'Vantage' else None
        
        impressions = random.randint(10000, 500000)
        views = int(impressions * random.uniform(0.3, 0.7))
        clicks = int(impressions * random.uniform(0.005, 0.03))
        conversions = int(clicks * random.uniform(0.05, 0.20))
        cost = round(random.uniform(500, 5000), 2)
        
        cpm = (cost / impressions * 1000) if impressions > 0 else 0
        cpc = (cost / clicks) if clicks > 0 else 0
        ctr = (clicks / impressions * 100) if impressions > 0 else 0
        conversion_rate = (conversions / clicks * 100) if clicks > 0 else 0
        
        cursor.execute("""
        INSERT INTO digital_advertising 
        (ad_id, campaign_id, platform, ad_name, ad_type, ad_format, placement, start_date, end_date, impressions, views, 
         clicks, conversions, cost, cpm, cpc, ctr, conversion_rate, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (f"AD-{platform[:3].upper()}-{i:04d}", campaign_id, platform, f"{platform} {ad_type.title()} Ad {i+1}", ad_type,
              random.choice(['standard', 'responsive', 'dynamic', 'native']), random.choice(['newsfeed', 'stories', 'sidebar', 'in-stream', 'banner']),
              start_date, end_date, impressions, views, clicks, conversions, cost, round(cpm, 2), round(cpc, 2), round(ctr, 3), round(conversion_rate, 2),
              now.isoformat(), now.isoformat()))
        ads_count += 1

    print(f"✅ Created {ads_count} digital advertising records")

    conn.commit()
    conn.close()
    
    print("\n✅ Marketing engagement data population complete!")
    print(f"Total records created:")
    print(f"  - {len(campaigns)} campaigns")
    print(f"  - {metrics_count} engagement metrics")
    print(f"  - {posts_count} social media posts")
    print(f"  - {emails_count} email marketing records")
    print(f"  - {ads_count} digital ads")


if __name__ == "__main__":
    populate()
