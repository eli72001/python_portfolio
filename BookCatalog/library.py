from book import Book

class BookCatalog():
    """Initializes a book catalog object
    """
    def __init__(self):
        self.book_catalog = []

    def add_book(self, title: str, author: str, genre: str):
        """ Adds book to the book catalog

        Args:
            title (str): title of book
            author (str): author of book
            genre (str): genre of the book
        """
        book_entry = Book(title, author, genre)
        self.book_catalog.append(book_entry)

    def view_books(self):
        """Prints the book catalog
        """
        for book in self.book_catalog:
            for item, value in book.book_dict.items():
                print(f'{item}: {value} ')
            print('\n')

    def search_book(self, keyword: str):
        """Searches book catalog based on keyword and returns all books 
            that contain a keyword in the author title or genre

        Args:
            keyword (str): keyword to search for
        """
        search_results = []
        for book in self.book_catalog:
            if keyword.lower() in book.book_dict['author'] or keyword.lower() in book.book_dict['title']:
                search_results.append(book)
        print("Search Results:\n")
        temp_catalog = BookCatalog()
        temp_catalog.book_catalog = search_results
        temp_catalog.view_books()

    def remove_book(self, title:str):
        """ Removes a book based on its title

        Args:
            title (str): title of book to be removed
        """
        for book in self.book_catalog:
            if book.getTitle() == title:
                self.book_catalog.remove(book)
                print("Book Removed")
                break
        else:
            print("Book not found.")
