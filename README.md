# Smart Shopping Assistant

A real-time product information pipeline that fetches product data and serves it through a high-performance Django REST API. The system is optimized for speed with caching and asynchronous processing.

## Features

- **Fast Product Search**: Search for products with sub-second response times
- **Caching Layer**: Intelligent caching to minimize API calls and improve performance
- **Scalable Architecture**: Built with scalability in mind using Celery for background tasks
- **RESTful API**: Clean, well-documented API endpoints
- **Admin Interface**: Built-in Django admin for managing data
- **Health Monitoring**: Built-in health check endpoints
  
## API POSTMAN SS
Search for products
<img width="1432" height="886" alt="image" src="https://github.com/user-attachments/assets/52339a35-32b6-47a1-bef8-1d1380a8cb08" />
Check Search History
<img width="1427" height="921" alt="image" src="https://github.com/user-attachments/assets/5ace3cbd-e94a-4c11-b984-bd40752282a6" />
Check for Health
<img width="1441" height="598" alt="image" src="https://github.com/user-attachments/assets/965af727-b438-47b4-8c10-4b7473a1a034" />





## Tech Stack

- **Backend**: Django 4.2
- **API**: Django REST Framework
- **Task Queue**: Celery with in-memory broker (Redis for production)
- **Caching**: Django's cache framework with local memory cache
- **Database**: SQLite (PostgreSQL ready for production)
- **Containerization**: Optional Docker support

## Prerequisites

- Python 3.8+
- pip (Python package manager)
- (Optional) Redis server for production

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/smart-shopping-assistant.git
   cd smart-shopping-assistant
   ```

2. **Create and activate a virtual environment**
   ```bash
   # On Windows
   python -m venv venv
   .\venv\Scripts\activate
   
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key-here
   REDIS_URL=redis://localhost:6379/0
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create a superuser (optional, for admin access)**
   ```bash
   python manage.py createsuperuser
   ```

## Running the Application

1. **Start Redis server**
   Make sure Redis is running on your system. On most systems, you can start it with:
   ```bash
   redis-server
   ```

2. **Start Celery worker** (in a new terminal)
   ```bash
   celery -A smart_shopper worker -l info -P gevent
   ```

3. **Start Celery beat** (in another terminal, for scheduled tasks)
   ```bash
   celery -A smart_shopper beat -l info
   ```

4. **Start the development server**
   ```bash
   python manage.py runserver
   ```

5. **Access the application**
   - API: http://127.0.0.1:8000/api/
   - Admin: http://127.0.0.1:8000/admin/
   - Health Check: http://127.0.0.1:8000/health/

## API Endpoints

### Search for Products
```
POST /api/search/
Content-Type: application/json

{
    "query": "organic peanut butter",
    "max_results": 10
}
```

### Get Product Details
```
GET /api/products/{product_id}/
```

### View Search History
```
GET /api/search/history/
```

### Health Check
```
GET /health/
```

## Running Tests

```bash
python manage.py test shopping.tests
```

## Production Deployment

For production deployment, consider the following:
1. Set `DEBUG=False` in your environment variables
2. Use a production-ready database like PostgreSQL
3. Set up a proper web server (Nginx + Gunicorn/uWSGI)
4. Configure HTTPS with Let's Encrypt
5. Set up proper monitoring and logging
6. Use environment variables for sensitive information


┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   API Layer     │    │   Task Queue    │    │   Data Store    │
│  (Django REST)  │───▶│    (Celery)     │───▶│    (SQLite)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
        ▲                      ▲
        │                      │
        ▼                      │
┌─────────────────┐    ┌─────────────────┐
│  Cache Layer    │    │  Web Scraping   │
│   (In-Memory)   │    │    (Async)      │
└─────────────────┘    └─────────────────┘

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Project Report

For detailed implementation details, challenges faced, and future improvements, see the [Project Report](REPORT.md).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Django and Django REST Framework
- Uses Redis for caching and task queuing
- Inspired by modern e-commerce search experiences
