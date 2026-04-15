// scheduler_graphics.cpp
// Compile: g++ scheduler_graphics.cpp -lgraphics -o scheduler_graphics.exe
// Note: Make sure graphics.h works with your compiler (Code::Blocks/WinBGI)

#include <graphics.h>
#include <conio.h>
#include <iostream>
#include <fstream>
#include <set>
#include <string>
#include <ctime>
#include <sstream>

using namespace std;

const int ROOMS = 10;
const int SLOTS = 15;
const int TOTAL = ROOMS * SLOTS;
const string BOOKINGS_FILE = "bookings.txt";
const string LOG_FILE = "booking_log.txt";

set<int> booked;
set<int> selected;

void log_action(const string &action, const string &details) {
    ofstream f(LOG_FILE, ios::app);
    if (!f) return;
    time_t t = time(nullptr);
    f << ctime(&t) << " | " << action << " | " << details << "\n";
}

void persist_save() {
    ofstream out(BOOKINGS_FILE, ios::trunc);
    if (!out) return;
    for (int b : booked) out << b << "\n";
}

void persist_load() {
    ifstream in(BOOKINGS_FILE);
    if (!in) return;
    booked.clear();
    int x;
    while (in >> x) {
        if (x >= 0 && x < TOTAL) booked.insert(x);
    }
}

string idx_to_label(int idx) {
    int room = idx / SLOTS + 1;
    int slot = idx % SLOTS + 1;
    return "Room " + to_string(room) + ", Slot " + to_string(slot);
}

string smart_book() {
    for (int i = 0; i < TOTAL; ++i) {
        if (!booked.count(i)) {
            booked.insert(i);
            persist_save();
            log_action("Smart Booking", idx_to_label(i));
            return "OK BOOKED " + idx_to_label(i);
        }
    }
    return "ERR No free slots.";
}

string manual_book(int r, int s) {
    if (r < 1 || r > ROOMS || s < 1 || s > SLOTS) return "ERR Invalid range.";
    int idx = (r-1)*SLOTS + (s-1);
    if (booked.count(idx)) return "ERR Already booked.";
    booked.insert(idx);
    persist_save();
    log_action("Manual Booking", idx_to_label(idx));
    return "OK BOOKED " + idx_to_label(idx);
}

string delete_book(int r, int s) {
    if (r < 1 || r > ROOMS || s < 1 || s > SLOTS) return "ERR Invalid range.";
    int idx = (r-1)*SLOTS + (s-1);
    if (!booked.count(idx)) return "ERR No booking found.";
    booked.erase(idx);
    persist_save();
    log_action("Deleted", idx_to_label(idx));
    return "OK DELETED " + idx_to_label(idx);
}

void draw_slots() {
    cleardevice();
    settextstyle(DEFAULT_FONT, HORIZ_DIR, 1);
    int margin = 50;
    int box_w = 50, box_h = 30;
    int spacing = 10;

    outtextxy(50, 10, "Smart Conference Scheduler");

    for (int r = 0; r < ROOMS; ++r) {
        string room_label = "Room " + to_string(r+1);
        outtextxy(10, margin + r*(box_h+spacing), room_label.c_str());

        for (int s = 0; s < SLOTS; ++s) {
            int idx = r*SLOTS + s;
            int x = 100 + s*(box_w+spacing);
            int y = margin + r*(box_h+spacing);

            if (booked.count(idx)) setfillstyle(SOLID_FILL, RED);
            else if (selected.count(idx)) setfillstyle(SOLID_FILL, ORANGE);
            else setfillstyle(SOLID_FILL, GREEN);

            bar(x, y, x+box_w, y+box_h);
            rectangle(x, y, x+box_w, y+box_h);

            string slot_text = to_string(s+1);
            outtextxy(x + 15, y + 8, slot_text.c_str());
        }
    }

    // Legend
    setfillstyle(SOLID_FILL, GREEN); bar(50, 600, 70, 620); outtextxy(80, 600, "Available");
    setfillstyle(SOLID_FILL, RED); bar(200, 600, 220, 620); outtextxy(230, 600, "Booked");
    setfillstyle(SOLID_FILL, ORANGE); bar(350, 600, 370, 620); outtextxy(380, 600, "Selected");
}

int get_slot_from_mouse(int mx, int my) {
    int margin = 50;
    int box_w = 50, box_h = 30;
    int spacing = 10;
    if (my < margin) return -1;
    int r = (my - margin) / (box_h+spacing);
    int s = (mx - 100) / (box_w+spacing);
    if (r < 0 || r >= ROOMS || s < 0 || s >= SLOTS) return -1;
    return r*SLOTS + s;
}

int main() {
    persist_load();
    int gd = DETECT, gm;
    initgraph(&gd, &gm, "");

    draw_slots();

    while (true) {
        if (kbhit()) {
            char ch = getch();
            if (ch == 27) break; // ESC to exit
            else if (ch == 's') { // smart book
                string out = smart_book();
                draw_slots();
            } else if (ch == 'c') { // clear selection
                selected.clear();
                draw_slots();
            } else if (ch == 'd') { // delete last selected
                for (auto it : selected) {
                    int r = it / SLOTS + 1;
                    int s = it % SLOTS + 1;
                    delete_book(r, s);
                }
                selected.clear();
                draw_slots();
            }
        }

        if (ismouseclick(WM_LBUTTONDOWN)) {
            int mx = mousex();
            int my = mousey();
            int idx = get_slot_from_mouse(mx, my);
            if (idx != -1 && !booked.count(idx)) {
                if (selected.count(idx)) selected.erase(idx);
                else selected.insert(idx);
                draw_slots();
            }
            clearmouseclick(WM_LBUTTONDOWN);
        }
    }

    closegraph();
    return 0;
}
