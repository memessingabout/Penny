import tkinter as tk
from tkinter import ttk

def apply_styles():
    style = ttk.Style()
    style.configure("TButton", padding=5, font=("Arial", 10))
    style.configure("Success.TButton", background="green", foreground="white")
    style.configure("Danger.TButton", background="red", foreground="white")
    style.configure("TLabel", font=("Arial", 10))
    style.configure("StatusBalanced.TLabel", foreground="green")
    style.configure("StatusOverbudget.TLabel", foreground="red")
    style.configure("StatusUnderbudget.TLabel", foreground="blue")