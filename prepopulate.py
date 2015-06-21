from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Base, Genre, Movie

engine = create_engine('sqlite:///moviescatalog.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Movies for Crime
genre1 = Genre(name="Crime")

session.add(genre1)
session.commit()

movie1 = Movie(
    name="The Shawshank Redemption",
    description="Two imprisoned men bond over a number of years, finding solace and eventual redemption through acts of common decency.",
    year="1994", director="Frank Darabont", genre=genre1
)

session.add(movie1)
session.commit()

movie2 = Movie(
    name="The Godfather",
    description="The aging patriarch of an organized crime dynasty transfers control of his clandestine empire to his reluctant son.",
    year="1972", director="Francis Ford Coppola", genre=genre1
)

session.add(movie2)
session.commit()

movie3 = Movie(
    name="The Godfather: Part II",
    description="The early life and career of Vito Corleone in 1920s New York is portrayed while his son, Michael, expands and tightens his grip on his crime syndicate stretching from Lake Tahoe, Nevada to pre-revolution 1958 Cuba.",
    year="1974", director="Francis Ford Coppola", genre=genre1
)

session.add(movie3)
session.commit()

movie4 = Movie(
    name="Pulp Fiction",
    description="The lives of two mob hit men, a boxer, a gangster's wife, and a pair of diner bandits intertwine in four tales of violence and redemption.",
    year="1994", director="Quentin Tarantino", genre=genre1
)

session.add(movie4)
session.commit()


# Movies for Action
genre2 = Genre(name="Action")

session.add(genre2)
session.commit()

movie1 = Movie(
    name="The Dark Knight",
    description="When the menace known as the Joker wreaks havoc and chaos on the people of Gotham, the caped crusader must come to terms with one of the greatest psychological tests of his ability to fight injustice.",
    year="2008", director="Christopher Nolan", genre=genre2
)

session.add(movie1)
session.commit()


# Movies for Drama
genre1 = Genre(name="Drama")

session.add(genre1)
session.commit()

movie1 = Movie(
    name="Schindler's List",
    description="In Poland during World War II, Oskar Schindler gradually becomes concerned for his Jewish workforce after witnessing their persecution by the Nazis.",
    year="1993", director="Steven Spielberg", genre=genre1
)

session.add(movie1)
session.commit()

movie2 = Movie(
    name="Fight Club",
    description="An insomniac office worker looking for a way to change his life crosses paths with a devil-may-care soap maker and they form an underground fight club that evolves into something much, much more...",
    year="1999", director="David Fincher", genre=genre1
)

session.add(movie2)
session.commit()

movie3 = Movie(
    name="12 Angry Men",
    description="A dissenting juror in a murder trial slowly manages to convince the others that the case is not as obviously clear as it seemed in court.",
    year="1957", director="Sidney Lumet", genre=genre1
)

session.add(movie3)
session.commit()

movie4 = Movie(
    name="The Good, the Bad and the Ugly",
    description="A bounty hunting scam joins two men in an uneasy alliance against a third in a race to find a fortune in gold buried in a remote cemetery.",
    year="1966", director="Sergio Leone", genre=genre1
)

session.add(movie4)
session.commit()


# Movies for Adventure
genre1 = Genre(name="Adventure")

session.add(genre1)
session.commit()


movie1 = Movie(
    name="The Lord of the Rings: The Return of the King",
    description="Gandalf and Aragorn lead the World of Men against Sauron's army to draw his gaze from Frodo and Sam as they approach Mount Doom with the One Ring.",
    year="2003", director="Peter Jackson", genre=genre1
)

session.add(movie1)
session.commit()

print "added movies"
