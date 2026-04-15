#include <iostream>
#include <vector>
#include <set>
#include <fstream>
#include <ctime>
#include <cmath>
using namespace std;

// ======================= Van Emde Boas Tree =======================
class VEBTree {
public:
    int u;
    int minVal, maxVal;
    VEBTree *summary;
    vector<VEBTree*> cluster;
    int lowerSqrtU, upperSqrtU;

    VEBTree(int u) {
        this->u = u;
        minVal = -1;
        maxVal = -1;
        if (u <= 2) {
            summary = nullptr;
        } else {
            lowerSqrtU = 1 << (int)(log2(u) / 2);
            upperSqrtU = u / lowerSqrtU;
            summary = nullptr;
            cluster.resize(upperSqrtU, nullptr);
        }
    }

    int high(int x) { return x / lowerSqrtU; }
    int low(int x) { return x % lowerSqrtU; }
    int index(int x, int y) { return x * lowerSqrtU + y; }

    bool isMember(int x) {
        if (x == minVal || x == maxVal) return true;
        if (u == 2) return false;
        if (cluster[high(x)] == nullptr) return false;
        return cluster[high(x)]->isMember(low(x));
    }

    void insertEmpty(int x) {
        minVal = maxVal = x;
    }

    void insert(int x) {
        if (minVal == -1) {
            insertEmpty(x);
            return;
        }
        if (x < minVal) swap(x, minVal);
        if (u > 2) {
            int hi = high(x);
            int lo = low(x);
            if (cluster[hi] == nullptr) cluster[hi] = new VEBTree(lowerSqrtU);
            if (cluster[hi]->minVal == -1) {
                if (summary == nullptr) summary = new VEBTree(upperSqrtU);
                summary->insert(hi);
                cluster[hi]->insertEmpty(lo);
            } else {
                cluster[hi]->insert(lo);
            }
        }
        if (x > maxVal) maxVal = x;
    }

    void remove(int x) {
        if (minVal == maxVal) {
            minVal = maxVal = -1;
        } else if (u == 2) {
            if (x == 0) minVal = 1; else minVal = 0;
            maxVal = minVal;
        } else {
            if (x == minVal) {
                int first_cluster = summary->minVal;
                if (first_cluster == -1) {
                    minVal = maxVal;
                    return;
                }
                x = index(first_cluster, cluster[first_cluster]->minVal);
                minVal = x;
            }
            int hi = high(x);
            int lo = low(x);
            if (cluster[hi] != nullptr) {
                cluster[hi]->remove(lo);
                if (cluster[hi]->minVal == -1) {
                    summary->remove(hi);
                    if (x == maxVal) {
                        if (summary->maxVal == -1)
                            maxVal = minVal;
                        else
                            maxVal = index(summary->maxVal, cluster[summary->maxVal]->maxVal);
                    }
                } else if (x == maxVal)
                    maxVal = index(hi, cluster[hi]->maxVal);
            }
        }
    }
};

// ----------------- Recursive VEB Dump -----------------
string dumpVEB(VEBTree* node, int indent = 0) {
    if (!node) return "";
    string s(indent, ' ');

    s += "Node(u=" + to_string(node->u) +
         ", min=" + to_string(node->minVal) +
         ", max=" + to_string(node->maxVal) + ")\n";

    if (node->u > 2 && node->summary) {
        s += string(indent + 2, ' ') + "Summary:\n";
        s += dumpVEB(node->summary, indent + 4);

        for (int i = 0; i < node->cluster.size(); i++) {
            if (node->cluster[i]) {
                s += string(indent + 2, ' ') + "Cluster[" + to_string(i) + "]:\n";
                s += dumpVEB(node->cluster[i], indent + 4);
            }
        }
    }
    return s;
}


// ======================= Conference Scheduler =======================
class ConferenceScheduler {
public:
    ConferenceScheduler() {
    int veb_size = 1;
    while (veb_size < total_slots) veb_size *= 2;
    veb = new VEBTree(veb_size);

    rebuildFromLog(); // <-- sync booked set from log at startup
}

    int rooms = 10;
    int slots = 15;
    int total_slots = rooms * slots;
    set<int> booked;
    VEBTree *veb;
    string logfile = "booking_log.txt";

    void logAction(string action, string details) {
        ofstream f(logfile, ios::app);
        time_t now = time(0);
        string t = ctime(&now);
        t.pop_back();
        f << t << " | " << action << ": " << details << endl;
    }

    string smartBooking() {
        for (int i = 0; i < total_slots; i++) {
            if (booked.find(i) == booked.end()) {
                booked.insert(i);
                veb->insert(i);
                logAction("Smart Booking", "Room " + to_string(i / slots + 1) + ", Slot " + to_string(i % slots + 1));
                return "Room " + to_string(i / slots + 1) + ", Slot " + to_string(i % slots + 1);
            }
        }
        return "No free slot available";
    }

    string manualBooking(int room, int slot) {
        int index = (room - 1) * slots + (slot - 1);
        if (booked.find(index) != booked.end()) return "Already booked";
        booked.insert(index);
        veb->insert(index);
        logAction("Manual Booking", "Room " + to_string(room) + ", Slot " + to_string(slot));
        return "Booked Room " + to_string(room) + ", Slot " + to_string(slot);
    }

    string deleteBooking(int room, int slot) {
        int index = (room - 1) * slots + (slot - 1);
        if (booked.find(index) == booked.end()) return "No booking found";
        booked.erase(index);
        veb->remove(index);
        logAction("Delete", "Room " + to_string(room) + ", Slot " + to_string(slot));
        return "Deleted Room " + to_string(room) + ", Slot " + to_string(slot);
    }

    void rebuildFromLog() {
    	ifstream f(logfile);
    	if (!f.is_open()) return;

    	string line;
    	while (getline(f, line)) {
        	size_t pos = line.find("Room ");
        	if (pos == string::npos) continue;

        	int room, slot;
        	if (sscanf(line.c_str() + pos, "Room %d, Slot %d", &room, &slot) != 2)
            	continue;

        	int index = (room - 1) * slots + (slot - 1);

        	if (line.find("Smart Booking") != string::npos || line.find("Manual Booking") != string::npos)
            booked.insert(index), veb->insert(index);
        	else if (line.find("Delete") != string::npos)
            booked.erase(index), veb->remove(index);
    }
}


    string summary() {
        int free = total_slots - booked.size();
        return "Rooms: " + to_string(rooms) +
               "\nSlots per Room: " + to_string(slots) +
               "\nFree Slots: " + to_string(free) +
               "\nBooked Slots: " + to_string(booked.size());
    }
};

// ======================= CLI bridge =======================
int main(int argc, char* argv[]) {
    static ConferenceScheduler scheduler;

    if (argc < 2) {
        cout << "Usage: backend <command> [args]\n";
        return 0;
    }

    string cmd = argv[1];

    if (cmd == "smart_book") {
        cout << scheduler.smartBooking();
    } else if (cmd == "manual_book" && argc == 4) {
        int r = stoi(argv[2]), s = stoi(argv[3]);
        cout << scheduler.manualBooking(r, s);
    } else if (cmd == "delete" && argc == 4) {
        int r = stoi(argv[2]), s = stoi(argv[3]);
        cout << scheduler.deleteBooking(r, s);
    } else if (cmd == "summary") {
        cout << scheduler.summary();
    } 
      else if (cmd == "dump_veb") {
    	cout << dumpVEB(scheduler.veb);
     }
      else {
        cout << "Invalid command.";
    }

    return 0;
}
