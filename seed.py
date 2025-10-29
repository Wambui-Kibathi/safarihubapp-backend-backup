from app import create_app, db
from models.destination import Destination
from sqlalchemy import text

app = create_app()

with app.app_context():
    # Clear existing destinations from the plural table
    db.session.execute(text('DELETE FROM destinations'))
    db.session.commit()

    destinations = [
        # Popular Destinations (Kenya)
        Destination(
            name="Maasai Mara",
            country="Kenya",
            price=250,
            image_url="https://images.unsplash.com/photo-1547471080-7cc2caa01a7e?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            description="Famous for the Great Migration.",
            category="popular"
        ),
        Destination(
            name="Amboseli National Park",
            country="Kenya",
            price=180,
            image_url="https://images.unsplash.com/photo-1578662996442-48f60103fc96?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            description="Known for views of Mount Kilimanjaro.",
            category="popular"
        ),
        Destination(
            name="Tsavo East National Park",
            country="Kenya",
            price=200,
            image_url="https://images.unsplash.com/photo-1544551763-46a013bb70d5?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            description="One of the largest parks in Kenya.",
            category="popular"
        ),
        Destination(
            name="Lamu Island",
            country="Kenya",
            price=150,
            image_url="https://images.unsplash.com/photo-1578662996442-48f60103fc96?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            description="Beautiful coastal island with Swahili culture.",
            category="popular"
        ),
        Destination(
            name="Nairobi National Park",
            country="Kenya",
            price=120,
            image_url="https://images.unsplash.com/photo-1544551763-46a013bb70d5?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            description="Safari park just outside the city.",
            category="popular"
        ),
        Destination(
            name="Mount Kenya",
            country="Kenya",
            price=220,
            image_url="https://images.unsplash.com/photo-1506905925346-21bda4d32df4?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            description="Second-highest mountain in Africa.",
            category="popular"
        ),

        # International Destinations
        Destination(
            name="Paris",
            country="France",
            price=900,
            image_url="https://images.unsplash.com/photo-1502602898536-47ad22581b52?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            description="The city of love and lights.",
            category="international"
        ),
        Destination(
            name="Tokyo",
            country="Japan",
            price=1200,
            image_url="https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            description="A modern city with rich traditions.",
            category="international"
        ),
        Destination(
            name="New York",
            country="USA",
            price=1100,
            image_url="https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            description="The city that never sleeps.",
            category="international"
        ),
        Destination(
            name="Rome",
            country="Italy",
            price=950,
            image_url="https://images.unsplash.com/photo-1552832230-c0197dd311b5?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            description="Home of the ancient Roman Empire.",
            category="international"
        ),
        Destination(
            name="Cape Town",
            country="South Africa",
            price=700,
            image_url="https://images.unsplash.com/photo-1580060839134-75a5edca2e99?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            description="Iconic landscapes and Table Mountain.",
            category="international"
        ),
        Destination(
            name="Dubai",
            country="UAE",
            price=1000,
            image_url="https://images.unsplash.com/photo-1512453979798-5ea266f8880c?ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D&auto=format&fit=crop&w=1000&q=80",
            description="Luxury city with futuristic architecture.",
            category="international"
        ),
    ]

    db.session.add_all(destinations)
    db.session.commit()

    print("12 destinations seeded successfully!")
