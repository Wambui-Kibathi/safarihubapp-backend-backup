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
            image_url="https://res.cloudinary.com/demo/image/upload/v1/maasai-mara.jpg",
            description="Famous for the Great Migration.",
            category="popular"
        ),
        Destination(
            name="Amboseli National Park",
            country="Kenya",
            price=180,
            image_url="https://res.cloudinary.com/demo/image/upload/v1/amboseli.jpg",
            description="Known for views of Mount Kilimanjaro.",
            category="popular"
        ),
        Destination(
            name="Tsavo East National Park",
            country="Kenya",
            price=200,
            image_url="https://res.cloudinary.com/demo/image/upload/v1/tsavo-east.jpg",
            description="One of the largest parks in Kenya.",
            category="popular"
        ),
        Destination(
            name="Lamu Island",
            country="Kenya",
            price=150,
            image_url="https://res.cloudinary.com/demo/image/upload/v1/lamu.jpg",
            description="Beautiful coastal island with Swahili culture.",
            category="popular"
        ),
        Destination(
            name="Nairobi National Park",
            country="Kenya",
            price=120,
            image_url="https://res.cloudinary.com/demo/image/upload/v1/nairobi-park.jpg",
            description="Safari park just outside the city.",
            category="popular"
        ),
        Destination(
            name="Mount Kenya",
            country="Kenya",
            price=220,
            image_url="https://res.cloudinary.com/demo/image/upload/v1/mount-kenya.jpg",
            description="Second-highest mountain in Africa.",
            category="popular"
        ),

        # International Destinations
        Destination(
            name="Paris",
            country="France",
            price=900,
            image_url="https://res.cloudinary.com/demo/image/upload/v1/paris.jpg",
            description="The city of love and lights.",
            category="international"
        ),
        Destination(
            name="Tokyo",
            country="Japan",
            price=1200,
            image_url="https://res.cloudinary.com/demo/image/upload/v1/tokyo.jpg",
            description="A modern city with rich traditions.",
            category="international"
        ),
        Destination(
            name="New York",
            country="USA",
            price=1100,
            image_url="https://res.cloudinary.com/demo/image/upload/v1/new-york.jpg",
            description="The city that never sleeps.",
            category="international"
        ),
        Destination(
            name="Rome",
            country="Italy",
            price=950,
            image_url="https://res.cloudinary.com/demo/image/upload/v1/rome.jpg",
            description="Home of the ancient Roman Empire.",
            category="international"
        ),
        Destination(
            name="Cape Town",
            country="South Africa",
            price=700,
            image_url="https://res.cloudinary.com/demo/image/upload/v1/cape-town.jpg",
            description="Iconic landscapes and Table Mountain.",
            category="international"
        ),
        Destination(
            name="Dubai",
            country="UAE",
            price=1000,
            image_url="https://res.cloudinary.com/demo/image/upload/v1/dubai.jpg",
            description="Luxury city with futuristic architecture.",
            category="international"
        ),
    ]

    db.session.add_all(destinations)
    db.session.commit()

    print("12 destinations seeded successfully!")
