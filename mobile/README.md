# Medhat Stocks Mobile

Native Flutter mobile frontend for Medhat Stocks.

The Streamlit app remains available separately. This folder is the real mobile application frontend and talks to the FastAPI backend.

Run locally:
flutter pub get
flutter run --dart-define=API_BASE=http://10.0.2.2:8000

For a physical phone, pass the LAN URL of the API instead of 10.0.2.2.
