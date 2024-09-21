import json
import sqlite3  
cx = sqlite3.connect("test.db")
import os

from .data_types import (
    Customer,
    Address,
    OpeningSchedule,
    Menu,
    Dish,
    Order,
    DeleteOrderResponse,
    SoupItem,
    BowlItem
)

days_of_week = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


class DataProvider:
    def __init__(self, db_path=None):
        if not db_path:
            self._current_path = os.path.dirname(os.path.realpath(__file__))
            db_path = os.path.join(self._current_path, "rice_up", "agent_lab.db")

        self.db_path = db_path
        self._conn = sqlite3.connect(self.db_path)
        self.create_rice_up_db()

    def create_rice_up_customers(self):
        cursor = self._conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS customers")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS customers (id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT, last_name TEXT, email TEXT, user_id TEXT, phone TEXT, special INTEGER, card_digits TEXT, street TEXT, city TEXT, state TEXT, zip TEXT, country TEXT)"
        )
        json_file = os.path.join(self._current_path, "rice_up", "customers.json")
        with open(json_file, "r") as file:
            data = json.load(file)
            try:
                for customer in data:
                    cursor.execute(
                        "INSERT INTO customers (first_name, last_name, email, user_id, phone, special, card_digits, street, city, state, zip, country) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            customer["firstname"],
                            customer["lastname"],
                            customer["email"],
                            customer["id"],
                            customer["phone"],
                            1 if customer["special"] == "true" else 0,
                            customer["card_digits"],
                            customer["address"]["street"],
                            customer["address"]["city"],
                            customer["address"]["state"],
                            customer["address"]["zip"],
                            customer["address"]["country"],
                        ),
                    )
            except Exception as e:
                print(f"Error: {e}")
        self._conn.commit()
        cursor.close()

    def is_special_client(self, user_id: str) -> bool:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = "SELECT * FROM customers WHERE user_id = ? AND special = ?"
        cursor.execute(query, (user_id, 1))
        result = cursor.fetchall()
        cursor.close()
        conn.close()
        return len(result) > 0

    def create_rice_up_menu(self):
            cursor = self._conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS rice_up_menu")
            cursor.execute(
                "CREATE TABLE IF NOT EXISTS rice_up_menu (id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT, menu TEXT)"
            )
            for day in days_of_week:
                    json_file = os.path.join(
                        self._current_path, "rice_up/menu", f"{day.lower()}.json"
                    )
                    with open(json_file, "r") as file:
                        menu = file.read()
                        try:
                            cursor.execute(
                                "INSERT INTO rice_up_menu (day, menu) VALUES (?,?)",
                                (day, menu),
                            )

                        except Exception as e:
                            print(f"Error: {e}")
            self._conn.commit()
            cursor.close()

    def create_rice_up_opening_hours(self):
        cursor = self._conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS opening_hours")
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS opening_hours
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, day text, is_special INTEGER, start TEXT, end text, status TEXT)"""
        )

        json_file = os.path.join(self._current_path, "rice_up", "openinghours.json")
        with open(json_file, "r") as file:
            data = json.load(file)
            for item in data["normal"]:
                cursor.execute(
                    "INSERT INTO opening_hours (day, is_special, start, end, status) VALUES (?, ?, ?, ?, ?)",
                    (item["day"], 0, item["start"], item["end"], item["status"]),
                )
            for item in data["special"]:
                cursor.execute(
                    "INSERT INTO opening_hours (day, is_special, start, end, status) VALUES (?, ?, ?, ?, ?)",
                    (item["day"], 1, item["start"], item["end"], item["status"]),
                )

        self._conn.commit()
        cursor.close()

    # create the orders table
    def create_rice_up_order(self):
        cursor = self._conn.cursor()
        cursor.execute("DROP TABLE IF EXISTS orders")
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, date TEXT, total REAL, detail TEXT, status TEXT)"
        )
        self._conn.commit()
        cursor.close()

    def create_rice_up_db(self):
        self.create_rice_up_menu()
        self.create_rice_up_opening_hours()
        self.create_rice_up_customers()
        self.create_rice_up_order()

    def get_rice_up_schedule(self, day: str, is_special: bool) -> OpeningSchedule:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = f"SELECT * FROM opening_hours WHERE day = ? AND is_special = ?"
        cursor.execute(query, (day, 1 if is_special else 0))
        row = cursor.fetchone()
        if not row:
            return None

        schedule = OpeningSchedule(day=row[1], start=row[3], end=row[4], status=row[5])
        cursor.close()
        conn.close()
        return schedule
    
    def get_rice_up_menu(self, day: str) -> Menu:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = "SELECT * FROM rice_up_menu where day = ?"
        cursor.execute(query, (day,))
        row = cursor.fetchone()
        if not row:
            return None
        cursor.close()
        conn.close()
        if not row or row[2] == "{}":
            return Menu(day=day, soup=[], bowl=[])

        menu = json.loads(row[2])
        return Menu(
            day=row[1],
            soup=[SoupItem(**item) for item in menu["soup"]],
            bowl=[BowlItem(**item) for item in menu["bowl"]],
        )
    
    def get_rice_up_dishes(self, day: str) -> dict[str, Dish]:
        menu = self.get_rice_up_menu(day)
        dishes = {}
        for item in menu.soup:
            dishes[item.name.lower()] = item
        for item in menu.bowl:
            dishes[item.name.lower()] = item
        return dishes
    
    def upsert_order(
        self, order_id: str | None, order: Order, status: str = "pending"
    ) -> str:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        if order_id:
            query = "UPDATE orders SET user_id = ?, date = ?, total = ?, detail = ?, status= ? WHERE id = ?"
            cursor.execute(
                query,
                (
                    order.user_id,
                    order.date,
                    order.total,
                    order.detail,
                    status,
                    int(order_id),
                ),
            )
        else:
            query = "INSERT INTO orders (user_id, date, total, detail, status) VALUES (?,?,?,?,?)"
            cursor.execute(
                query,
                (order.user_id, order.date, order.total, order.detail, status),
            )
            order_id = f"{cursor.lastrowid:04}"
        conn.commit()
        cursor.close()
        return order_id

    def get_rice_up_orders(self, user_id: str, status: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = "SELECT * FROM orders WHERE status = ? and user_id = ?"
        cursor.execute(query, (status, user_id))
        rows = cursor.fetchall()
        if not rows:
            return []
        cursor.close()
        conn.close()
        return [
            Order(
                id=f"{row[0]:04}",
                user_id=row[1],
                date=row[2],
                total=float(row[3]),
                detail=row[4],
                status=row[5],
            )
            for row in rows
        ]

    def get_rice_up_order(self, user_id: str, order_id: str, status: str) -> Order:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = "SELECT * FROM orders WHERE id = ? and user_id = ? and status = ?"
        cursor.execute(query, (order_id, user_id, status))
        row = cursor.fetchone()
        if not row:
            return None
        cursor.close()
        conn.close()
        return Order(
            id=f"{row[0]:04}",
            user_id=row[1],
            date=row[2],
            total=float(row[3]),
            detail=row[4],
            status=row[5],
        )

    def cancel_rice_up_order(self, user_id: str, order_id: str) -> DeleteOrderResponse:
        order = self.get_rice_up_order(user_id=user_id, order_id=order_id, status="pending")
        if not order:
            return DeleteOrderResponse(message="Order not found.", status="failed")
        self.upsert_order(order_id, order, "canceled")
        return DeleteOrderResponse(
            message="Order successfully cancelled.", status="success"
        )
    
    def set_rice_up_order_status(self, order_id: str, status: str) -> bool:
        order = self.get_rice_up_order(order_id)
        if not order:
            return False
        self.upsert_rice_up_order(order_id, order, status)
        return True
    
    # Returns the client information
    def get_rice_up_customer(self, user_id: str) -> Customer:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = "SELECT * FROM customers WHERE user_id = ?"
        cursor.execute(query, (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        if not row:
            return None
        return Customer(
            first_name=row[1],
            last_name=row[2],
            email=row[3],
            user_id=row[4],
            phone=row[5],
            special=row[6] == 1,
            card_digits=row[7],
            address=Address(
                street=row[8], city=row[9], state=row[10], zip=row[11], country=row[12]
            ),
        )
    
    def add_customer(self, customer: Customer):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        query = "INSERT INTO customers (first_name, last_name, email, user_id, phone, special, card_digits, street, city, state, zip, country) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)"
        cursor.execute(
            query,
            (
                customer.first_name,
                customer.last_name,
                customer.email,
                customer.user_id,
                customer.phone,
                1 if customer.special else 0,
                customer.card_digits,
                customer.address.street,
                customer.address.city,
                customer.address.state,
                customer.address.zip,
                customer.address.country,
            ),
        )
        conn.commit()
        cursor.close()