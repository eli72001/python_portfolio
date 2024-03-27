"""Class representing a Book
"""
class Book():
    """Every Book has a title, author, and genre
    """
    def __init__(self, title: str, author: str, genre: str):
        self.book_dict = {'title': title, 'author': author, 'genre': genre}

    def getTitle(self):
        """Return title of book

        Returns:
            str: title of book
        """
        return self.book_dict['title']

    def getAuthor(self):
        """ Return author of book

        Returns:
            str: author of book
        """
        return self.book_dict['author']

    def getGenre(self):
        """ Return author of book

        Returns:
            str: author
        """
        return self.book_dict['genre']
