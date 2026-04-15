# Smart Conference Room Scheduler using Van Emde Boas Tree

## Overview
This project is a **Smart Conference Room Scheduler** designed to manage reservations across **10 conference rooms**, each having **15 available time slots per day**.

The system uses a **Van Emde Boas Tree (vEB Tree)** as its primary data structure to store and look up booked slots. The vEB Tree enables extremely fast search and update operations with a time complexity of **O(log log n)**, making it more efficient than traditional binary search trees or hash tables when handling time-indexed scheduling operations.

---

## Key Functionalities

### Smart Booking
Automatically finds the **earliest available time slot** in any conference room and books it without requiring the user to manually choose a room or slot.

### Manual Booking
Allows the user to **select a specific room and time slot** for reservation.

### Delete Booking
Enables removal of any existing reservation from the schedule.

### View Bookings
Displays all current reservations in a **clear and readable format**.

---

## Graphical User Interface

The system includes a **Tkinter-based graphical interface** that visually represents conference rooms and their available time slots.

Slots are **color-coded** to indicate:

- Available slots
- Booked slots
- Currently selected slot during booking actions

This visual layout helps users quickly identify availability and make booking decisions efficiently.

---

## Logging

All system operations such as:

- Booking creation
- Booking deletion
- System actions

are recorded in a **log file**. This ensures transparency, provides a usage history, and supports auditing or debugging when required.

---

## Technologies Used

- C++
- Python
- Tkinter GUI
- Van Emde Boas Tree Data Structure
- Makefile-based build system
