from app import create_app

# Create the app instance using our factory function
app = create_app()

if __name__ == '__main__':
    # debug=True automatically reloads the server whenever you edit a file!
    app.run(debug=True, port=5000)