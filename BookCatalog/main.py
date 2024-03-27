"""Book Catalog Module"""
from library import BookCatalog

my_catalog = BookCatalog()
while True:

    print("1. Add Book")
    print("2. View Books")
    print("3. Search Book")
    print("4. Remove Book")
    print("5. Exit")

    choice = input("Enter your choice: ")

    if choice == '1':
        title = input("Enter book title: ")
        author = input("Enter author: ")
        genre = input("Enter genre: ")
        my_catalog.add_book(title, author, genre)

    elif choice == '2':
        print("Books:\n")
        my_catalog.view_books()

    elif choice == '3':
        keyword = input("Enter search keyword: ")
        my_catalog.search_book(keyword)

    elif choice == '4':
        title = input("Enter title of book to remove: ")
        my_catalog.remove_book(title)

    elif choice == '5':
        print("Exiting.")
        break

    else:
        print("Invalid choice.")
