import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import requests
from server import start_proxy_server
import threading
import base64
import json
from auth import load_users

class ProxyGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Proxy Server GUI")
        self.root.geometry("800x600")
        
        self.server_running = False
        self.server_thread = None
        self.server = None
        self.proxy_port = 3001
        
        # Start server automatically
        self.start_server()
        
        # Create login frame
        self.login_frame = ttk.Frame(self.root)
        self.setup_login_frame()
        self.login_frame.pack(fill='both', expand=True)
        
        # Create main frame (initially hidden)
        self.main_frame = ttk.Frame(self.root)
        self.setup_main_frame()
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_login_frame(self):
        ttk.Label(self.login_frame, text="Login", font=('Arial', 20)).pack(pady=20)
        
        # Username
        ttk.Label(self.login_frame, text="Username:").pack(pady=5)
        self.username_var = tk.StringVar()
        ttk.Entry(self.login_frame, textvariable=self.username_var).pack(pady=5)
        
        # Password
        ttk.Label(self.login_frame, text="Password:").pack(pady=5)
        self.password_var = tk.StringVar()
        ttk.Entry(self.login_frame, textvariable=self.password_var, show="*").pack(pady=5)
        
        # Login button
        ttk.Button(self.login_frame, text="Login", command=self.login).pack(pady=20)
        
    def setup_main_frame(self):
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Proxy tab
        proxy_frame = ttk.Frame(self.notebook)
        self.notebook.add(proxy_frame, text='Proxy')
        
        # Server control
        control_frame = ttk.Frame(proxy_frame)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        self.server_btn = ttk.Button(control_frame, text="Start Server", 
                                   command=self.toggle_server)
        self.server_btn.pack(side='left', padx=5)
        
        # URL input
        url_frame = ttk.Frame(proxy_frame)
        url_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Label(url_frame, text="URL:").pack(side='left', padx=5)
        self.url_var = tk.StringVar()
        ttk.Entry(url_frame, textvariable=self.url_var).pack(side='left', 
                                                            fill='x', expand=True, padx=5)
        ttk.Button(url_frame, text="Send Request", 
                  command=self.send_request).pack(side='left', padx=5)
        
        # Response area
        ttk.Label(proxy_frame, text="Response:").pack(anchor='w', padx=10, pady=5)
        self.response_area = scrolledtext.ScrolledText(proxy_frame, height=20)
        self.response_area.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Admin tab
        self.admin_frame = ttk.Frame(self.notebook)
        self.setup_admin_frame()
        # Admin tab will be added only for admin users
        
    def login(self):
        username = self.username_var.get()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return
            
        # Create basic auth header
        auth_string = f"{username}:{password}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        # Make sure server is running
        if not self.server_running:
            if not self.start_server():
                return
                
        # Test authentication with analytics endpoint
        try:
            response = requests.get(
                f"http://localhost:{self.proxy_port}/analytics",
                headers={"Authorization": f"Basic {auth_b64}"}
            )
            
            if response.status_code == 200:
                # Load user details
                users_db = load_users()
                user = users_db.get(username)
                
                self.login_frame.pack_forget()
                self.main_frame.pack(fill='both', expand=True)
                self.auth_header = f"Basic {auth_b64}"
                self.server_btn.config(text="Stop Server")
                
                # Show admin tab if user is admin
                if user and user.get("role") == "Admin":
                    self.notebook.add(self.admin_frame, text='User Management')
                    self.refresh_user_list()
            else:
                messagebox.showerror("Error", "Invalid credentials")
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Error", "Failed to connect to server. Please try again.")
    
    def start_server(self):
        if not self.server_running:
            try:
                import uvicorn
                import asyncio
                
                def run_server():
                    config = uvicorn.Config(app="server:app", host="0.0.0.0", port=self.proxy_port)
                    self.server = start_proxy_server(self.proxy_port, config)
                    
                    # Create new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Run the server
                    loop.run_until_complete(self.server.serve())
                    loop.close()
                
                self.server_thread = threading.Thread(target=run_server)
                self.server_thread.daemon = True
                self.server_thread.start()
                self.server_running = True
                
                # Wait a bit for the server to start
                import time
                time.sleep(2)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to start server: {str(e)}")
                return False
        return True

    def stop_server(self):
        if self.server_running and self.server:
            try:
                self.server.should_exit = True
                self.server_running = False
                self.server = None
                # Wait for server to stop
                import time
                time.sleep(1)
                return True
            except Exception as e:
                messagebox.showerror("Error", f"Failed to stop server: {str(e)}")
                return False
        return True

    def toggle_server(self):
        if not self.server_running:
            if self.start_server():
                self.server_btn.config(text="Stop Server")
                messagebox.showinfo("Success", f"Server started on port {self.proxy_port}")
        else:
            if self.stop_server():
                self.server_btn.config(text="Start Server")
                messagebox.showinfo("Success", "Server stopped successfully")
    
    def send_request(self):
        url = self.url_var.get()
        if not url:
            messagebox.showerror("Error", "Please enter a URL")
            return
            
        try:
            response = requests.get(
                f"http://localhost:{self.proxy_port}/?url={url}",
                headers={"Authorization": self.auth_header}
            )
            self.response_area.delete(1.0, tk.END)
            self.response_area.insert(tk.END, response.text)
        except requests.exceptions.ConnectionError:
            messagebox.showerror("Error", "Failed to connect to proxy server")
    
    def setup_admin_frame(self):
        # Left side - User List
        list_frame = ttk.Frame(self.admin_frame)
        list_frame.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        
        ttk.Label(list_frame, text="Users:").pack(anchor='w')
        self.user_list = ttk.Treeview(list_frame, columns=('Username', 'Role'), 
                                    show='headings', height=10)
        self.user_list.heading('Username', text='Username')
        self.user_list.heading('Role', text='Role')
        self.user_list.pack(fill='both', expand=True)
        
        # Right side - Add User Form
        form_frame = ttk.Frame(self.admin_frame)
        form_frame.pack(side='right', fill='y', padx=5, pady=5)
        
        ttk.Label(form_frame, text="Add New User", font=('Arial', 12, 'bold')).pack(pady=10)
        
        ttk.Label(form_frame, text="Username:").pack(anchor='w')
        self.new_username = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_username).pack(fill='x', pady=2)
        
        ttk.Label(form_frame, text="Password:").pack(anchor='w')
        self.new_password = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.new_password, show="*").pack(fill='x', pady=2)
        
        ttk.Label(form_frame, text="Role:").pack(anchor='w')
        self.new_role = tk.StringVar(value="Student")
        role_combo = ttk.Combobox(form_frame, textvariable=self.new_role, 
                                values=["Admin", "Student", "Teacher"])
        role_combo.pack(fill='x', pady=2)
        
        ttk.Button(form_frame, text="Add User", 
                  command=self.add_user).pack(fill='x', pady=10)
        
        # Refresh button
        ttk.Button(form_frame, text="Refresh List", 
                  command=self.refresh_user_list).pack(fill='x', pady=5)

    def refresh_user_list(self):
        # Clear existing items
        for item in self.user_list.get_children():
            self.user_list.delete(item)
        
        # Load and display users
        users_db = load_users()
        for username, user in users_db.items():
            self.user_list.insert('', 'end', values=(username, user.get('role', 'Student')))

    def add_user(self):
        username = self.new_username.get()
        password = self.new_password.get()
        role = self.new_role.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please fill in all fields")
            return
            
        try:
            # Load current users
            with open("users.json", "r") as f:
                data = json.load(f)
            
            # Check if username already exists
            if any(u["username"] == username for u in data["users"]):
                messagebox.showerror("Error", "Username already exists")
                return
            
            # Add new user
            data["users"].append({
                "username": username,
                "password": password,
                "role": role
            })
            
            # Save updated users
            with open("users.json", "w") as f:
                json.dump(data, f, indent=2)
            
            # Clear form
            self.new_username.set("")
            self.new_password.set("")
            self.new_role.set("Student")
            
            # Refresh list
            self.refresh_user_list()
            messagebox.showinfo("Success", "User added successfully")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to add user: {str(e)}")

    def on_closing(self):
        """Handle window closing event"""
        if self.server_running:
            self.stop_server()
        self.root.destroy()

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = ProxyGUI()
    app.run()