from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Categories, BASE, CategoryItems, Users
import datetime

ENGINE = create_engine(
    'postgresql+psycopg2://nikitas:nikitas@localhost/itemcatalog')

BASE.metadata.bind = ENGINE
DB_SESSION = sessionmaker(bind=ENGINE)
session = DB_SESSION()

# Categories.
category1 = Categories(name="Meat")

session.add(category1)
session.commit()

category2 = Categories(name="Fruits")

session.add(category2)
session.commit()

category3 = Categories(name="Vegetables")

session.add(category3)
session.commit()

# Items for category 1.
categoryItem1 = CategoryItems(name="Pork", content="The flesh of a pig used as"
                              " food, especially when uncured.",
                              category_id=1, user_id=1,
                              date_time=datetime.datetime.now())
session.add(categoryItem1)
session.commit()

categoryItem2 = CategoryItems(name="Bacon", content="Cured meat from the back "
                              "or sides of a pig.",
                              category_id=1, user_id=1,
                              date_time=datetime.datetime.now())
session.add(categoryItem2)
session.commit()

# Items for category 2.
categoryItem3 = CategoryItems(name="Pineapple", content="A large juicy "
                              "tropical fruit consisting of aromatic edible "
                              "yellow flesh surrounded by a tough segmented "
                              "skin and topped with a tuft of stiff leaves.",
                              category_id=2, user_id=1,
                              date_time=datetime.datetime.now())
session.add(categoryItem3)
session.commit()

categoryItem4 = CategoryItems(name="Apple", content="The round fruit of a tree"
                              " of the rose family, which typically has thin "
                              "green or red skin and crisp flesh.",
                              category_id=2, user_id=1,
                              date_time=datetime.datetime.now())
session.add(categoryItem4)
session.commit()

# Items for category 3.
categoryItem5 = CategoryItems(name="Lettuce", content="A cultivated plant of "
                              "the daisy family, with edible leaves that are "
                              "eaten in salads.", category_id=3, user_id=1,
                              date_time=datetime.datetime.now())
session.add(categoryItem5)
session.commit()

categoryItem6 = CategoryItems(name="Broccoli", content="A cultivated variety "
                              "of cabbage bearing heads of green or purplish "
                              "flower buds that are eaten as a vegetable.",
                              category_id=3, user_id=1,
                              date_time=datetime.datetime.now())

session.add(categoryItem6)
session.commit()

print("Database ready!")
