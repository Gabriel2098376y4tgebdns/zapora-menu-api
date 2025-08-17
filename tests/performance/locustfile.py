"""
Performance testing with Locust for Zapora API
Tests load capacity and response times under stress
"""
from locust import HttpUser, task, between
import random


class ZaporaAPIUser(HttpUser):
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    
    def on_start(self):
        """Called when a user starts"""
        # Login and get token if needed
        pass
    
    @task(3)
    def view_menu(self):
        """View menu items - most common action"""
        self.client.get("/menu/items/")
    
    @task(2)
    def view_categories(self):
        """View menu categories"""
        self.client.get("/menu/categories/")
    
    @task(1)
    def search_items(self):
        """Search for menu items"""
        search_terms = ["pizza", "burger", "salad", "drink", "dessert"]
        term = random.choice(search_terms)
        self.client.get(f"/menu/items/?search={term}")
    
    @task(1)
    def health_check(self):
        """Health check endpoint"""
        self.client.get("/healthz")
    
    @task(1)
    def api_docs(self):
        """API documentation access"""
        self.client.get("/docs")
