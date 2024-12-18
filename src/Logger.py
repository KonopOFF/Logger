import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3, datetime, time, db
from maidenhead import to_location
from geopy.distance import geodesic
#from qrz import QRZ

from qrz import QRZ
import time
import math




# Zmienna globalna dla Twojego lokatora
my_grid_square = ""
my_callsign = ""

# Funkcja ustawiająca ciemny motyw
def set_dark_mode(widget):
    widget.tk_setPalette(background='#2E2E2E', foreground='#FFFFFF', 
                         activeBackground='#3E3E3E', activeForeground='#FFFFFF',
                         highlightBackground='#3E3E3E', highlightColor='#FFFFFF',
                         insertBackground='#FFFFFF', selectBackground='#5E5E5E',
                         selectForeground='#FFFFFF', disabledForeground='#4E4E4E')

    style = ttk.Style()
    style.theme_use('clam')
    style.configure('TButton', background='#4E4E4E', foreground='#FFFFFF')
    style.map('TButton', background=[('active', '#5E5E5E')])
    style.configure('TLabel', background='#2E2E2E', foreground='#FFFFFF')
    style.configure('TEntry', fieldbackground='#3E3E3E', foreground='#FFFFFF')
    style.configure('TCombobox', fieldbackground='#3E3E3E', foreground='#FFFFFF')
    style.configure('Treeview', background='#3E3E3E', foreground='#FFFFFF', fieldbackground='#3E3E3E')
    style.configure('Treeview.Heading', background='#4E4E4E', foreground='#FFFFFF')

    



# Funkcja do obliczania odległości między grid square
def calculate_distance(my_grid, their_grid):
    my_location = to_location(my_grid)
    their_location = to_location(their_grid)
    distance = geodesic(my_location, their_location).km
    return int(distance)

# Funkcja do usuwania danych z bazy




# Funkcja eksportu do pliku ADIF
def export_adif():
    # Połączenie z bazą danych
    conn = sqlite3.connect("logbook.db")
    cursor = conn.cursor()
    
    # Pobranie wszystkich rekordów z bazy
    cursor.execute("SELECT * FROM logbook")
    rows = cursor.fetchall()
    conn.close()
    
    # Wybór lokalizacji i nazwy pliku
    adif_file = filedialog.asksaveasfilename(defaultextension=".adi", filetypes=[("ADIF Files", "*.adi")])
    if not adif_file:
        return  # Jeśli użytkownik anulował zapis, zakończ funkcję
    
    with open(adif_file, "w") as f:
        # Nagłówek ADIF
        f.write("<ADIF_VER:5>3.0\n")  # Wersja ADIF
        f.write("<PROGRAMID:15>Python Logger\n")  # Program, który wygenerował plik
        f.write("<EOH>\n")  # Zakończenie nagłówka

        # Zapis danych QSO
        for row in rows:
            qso_date = row[1]  # Data QSO
            callsign = row[2]  # Znak wywoławczy
            rst_sent = row[3]
            rst_rcvd = row[4]
            band = row[5]  # Pasmo
            mode = row[6]
            tx_pwr = row[7]  #moc
            grid_square = row[8]  # Lokator grid
            distance = row[9]
            name = row[10]
              # Dystans
            comment = row[12]  # Komentarz
            country = row[11]
            # Tworzenie rekordu QSO w formacie ADIF
            f.write(f"<QSO_DATE:{len(qso_date)}>{qso_date} ")
            f.write(f"<CALL:{len(callsign)}>{callsign} ")
            f.write(f"<BAND:{len(band)}>{band} ")
            f.write(f"<MODE:{len(mode)}>{mode} ")
            f.write(f"<GRIDSQUARE:{len(grid_square)}>{grid_square} ")
            f.write(f"<DISTANCE:{len(str(distance))}>{distance} km ")
            f.write(f"<COMMENT:{len(comment)}>{comment} ")
            f.write("<EOR>\n")  # Zakończenie rekordu QSO
        
    # Powiadomienie o sukcesie
    messagebox.showinfo("Eksport ADIF", f"Pomyślnie wyeksportowano do pliku: {adif_file}")


# Funkcja do pobierania danych z QRZ


def fetch_qrz_data(callsign):
    qrz = QRZ(cfg='./settings.cfg')
    result = qrz.callsign(callsign)
    print("QRZ result:", result)  # Logowanie wyniku z QRZ
    if result:
        data = {
            "name": result.get('fname') + " " + result.get('name'),
            "country": result.get('country'),
        }
        city = result.get('addr2')
        country = result.get('country')
        print("City:", city)  # Logowanie nazwy miasta
        print("Country:", country)  # Logowanie kraju
        if city and country:
            coords = fetch_coordinates(city, country)
            if coords:
                data["latitude"] = coords[0]
                data["longitude"] = coords[1]
                data["locator"] = latlon_to_locator(float(coords[0]), float(coords[1]))
                print(f"Współrzędne miasta {city}: Lat = {coords[0]}, Lon = {coords[1]}")
                print(f"Locator: {data['locator']}")
        return data
    else:
        messagebox.showerror("Błąd", "Nie udało się pobrać danych z QRZ")
        return None

def fetch_coordinates(city, country):
    url = f"https://nominatim.openstreetmap.org/search?q={city},{country}&format=json&limit=1"
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; MyApp/1.0; +http://myapp.com)'}
    response = requests.get(url, headers=headers)
    print("Request URL:", url)  # Logowanie URL zapytania
    print("Response status code:", response.status_code)  # Logowanie kodu statusu odpowiedzi
    if response.status_code == 200 and response.json():
        result = response.json()[0]
        print("OpenStreetMap result:", result)  # Logowanie wyniku z OpenStreetMap
        return (result['lat'], result['lon'])
    else:
        messagebox.showerror("Błąd", "Nie udało się pobrać współrzędnych z OpenStreetMap")
        return None

def latlon_to_locator(lat, lon):
    """
    Konwersja współrzędnych geograficznych na lokator Grid (Maidenhead Locator System)
    """
    lat += 90.0
    lon += 180.0
    A = chr(int(lon / 20) + ord('A'))
    B = chr(int(lat / 10) + ord('A'))
    lon %= 20
    lat %= 10
    a = chr(int(lon / 2) + ord('0'))
    b = chr(int(lat) + ord('0'))
    lon = (lon % 2) * 60
    lat = (lat - int(lat)) * 60
    aa = chr(int(lon / 5) + ord('A'))
    bb = chr(int(lat / 2.5) + ord('A'))
    return A + B + a + b + aa + bb

# Funkcja do automatycznego wypełniania danych z QRZ
"""
def auto_fill_qrz():
    callsign = callsign_entry.get()
    if not callsign:
        messagebox.showwarning("Ostrzeżenie", "Proszę wprowadzić znak wywoławczy")
        return

    data = fetch_qrz_data(callsign)
    if data:
        name_entry.delete(0, tk.END)
        name_entry.insert(0, data["name"])
        country_entry.delete(0, tk.END)
        country_entry.insert(0, data["country"])
        if "locator" in data:
            grid_square_entry.delete(0, tk.END)
            grid_square_entry.insert(0, data["locator"])
"""
# Funkcja do dodawania wpisów
def add_entry():
    their_grid = grid_square_entry.get()
    if their_grid:
        distance = calculate_distance(my_grid_square, their_grid)
    else:
        distance = None  # Można też ustawić 0, jeśli to bardziej sensowne

    entry_data = (
        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        callsign_entry.get(),
        rst_sent_entry.get(),
        rst_received_entry.get(),
        band_combobox.get(),
        mode_combobox.get(),
        power_entry.get(),
        grid_square_entry.get(),
        distance,
        name_entry.get(),
        country_entry.get(),
        comment_entry.get()
    )
    add_to_database(entry_data)
    update_table()
    clear_entries()
    show_temporary_message("QSO zostało dodane!", 3000)

# Funkcja do wyświetlania tymczasowego komunikatu
def show_temporary_message(message, duration):
    # Tworzymy etykietę nad tabelką
    message_label = tk.Label(root, text=message, fg="green", font=("Arial", 12))
    message_label.pack(pady=5)  # Umieszczamy ją z niewielkim odstępem nad tabelką

    # Usunięcie komunikatu po upływie `duration` milisekund
    root.after(duration, message_label.destroy)



# Funkcja do załadowania danych z pliku konfiguracyjnego
def load_config():
    global my_grid_square, my_callsign
    try:
        with open("config.txt", "r") as config_file:
            lines = config_file.readlines()
            # Zakładając, że w pliku są tylko dwie linie: Lokator i Znak wywoławczy
            my_grid_square = lines[0].strip().split(":")[1].strip()
            my_callsign = lines[1].strip().split(":")[1].strip()
    except FileNotFoundError:
        # Jeżeli plik nie istnieje, zwróć domyślne wartości
        my_grid_square, my_callsign = "", ""

# Funkcja do zmiany lokatora i znaku wywoławczego
def change_grid_square():
    global my_grid_square, my_callsign
    
    config_window = tk.Toplevel(root)
    config_window.title("Konfiguracja")

    # Załaduj aktualne dane konfiguracyjne
    load_config()

    tk.Label(config_window, text="Lokator Grid").grid(row=0, column=0)
    grid_entry = tk.Entry(config_window)
    grid_entry.insert(0, my_grid_square)  # Wstawienie obecnego lokatora
    grid_entry.grid(row=0, column=1)

    tk.Label(config_window, text="Znak wywoławczy").grid(row=1, column=0)
    callsign_entry = tk.Entry(config_window)
    callsign_entry.insert(0, my_callsign)  # Wstawienie obecnego znaku wywoławczego
    callsign_entry.grid(row=1, column=1)

    def save_config():
        global my_grid_square, my_callsign
        my_grid_square = grid_entry.get()
        my_callsign = callsign_entry.get()
        if my_grid_square and my_callsign:
            # Zapisz nowe wartości do pliku konfiguracyjnego
            with open("config.txt", "w") as config_file:
                config_file.write(f"Grid: {my_grid_square}\nCallsign: {my_callsign}\n")
            config_window.destroy()
            messagebox.showinfo("Informacja", "Konfiguracja zapisana")
        else:
            messagebox.showwarning("Ostrzeżenie", "Proszę wprowadzić wszystkie wartości")

    tk.Button(config_window, text="Zapisz", command=save_config).grid(row=2, column=0, columnspan=2, pady=10)
    

def distance_between_grids(grid1, grid2):
    def grid_to_latlon(grid):
        grid = grid.upper()
        lon = (ord(grid[0]) - ord('A')) * 20 - 180 + (ord(grid[2]) - ord('0')) * 2 + (ord(grid[4]) - ord('A')) / 12
        lat = (ord(grid[1]) - ord('A')) * 10 - 90 + (ord(grid[3]) - ord('0')) + (ord(grid[5]) - ord('A')) / 24
        return lat, lon

    lat1, lon1 = grid_to_latlon(grid1)
    lat2, lon2 = grid_to_latlon(grid2)

    R = 6371  # Promień Ziemi w kilometrach
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2) * math.sin(dlat / 2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) * math.sin(dlon / 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return distance


# Funkcja do usuwania wpisów
def delete_entry():
    selected_item = table.selection()
    if not selected_item:
        messagebox.showwarning("Ostrzeżenie", "Proszę zaznaczyć wpis do usunięcia")
        return

    callsign = table.item(selected_item)["values"][1]
    db.delete_from_database(callsign)
    table.delete(selected_item)
    messagebox.showinfo("Usunięto", "QSO zostało usunięte!")

# Czyszczenie pól
def clear_entries():
    callsign_entry.delete(0, tk.END)
    rst_sent_entry.delete(0, tk.END)
    rst_sent_entry.insert(0, "59")  # Ustawienie domyślnego 59
    rst_received_entry.delete(0, tk.END)
    rst_received_entry.insert(0, "59")  # Ustawienie domyślnego 59
    grid_square_entry.delete(0, tk.END)
    name_entry.delete(0, tk.END)
    country_entry.delete(0, tk.END)
    comment_entry.delete(0, tk.END)


# Funkcja do aktualizacji zegara UTC
def update_utc_clock(label):
    current_time = time.strftime('%H:%M:%S', time.gmtime())  # Pobieranie czasu UTC
    label.config(text=current_time)  # Aktualizacja tekstu etykiety
    label.after(1000, update_utc_clock, label)  # Ustawienie ponownej aktualizacji za 1000ms (1 sekunda)

# GUI aplikacji
root = tk.Tk()
root.title("LogBook SP9OFF&SQ4UVB")

load_config()

# Menu
menu = tk.Menu(root)
root.config(menu=menu)

settings_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Menu", menu=settings_menu)
settings_menu.add_command(label="Konfiguracja", command=change_grid_square)

# Przeniesienie przycisku eksportowania do menu
settings_menu.add_command(label="Eksportuj ADIF", command=export_adif)

# Ustawienie ciemnego motywu
set_dark_mode(root)

# Górna sekcja - formularz
form_frame = tk.Frame(root, padx=10, pady=10)
form_frame.pack(fill=tk.X)

# Ramka na zegar UTC
utc_frame = tk.Frame(root, padx=10, pady=5, relief="solid", bd=1)  # Ramka z cieniem wokół zegara
utc_frame.pack(anchor="nw", padx=10, pady=10)

# Etykieta z napisem "UTC"
utc_label_text = tk.Label(utc_frame, text="UTC:", font=("Helvetica", 14), anchor="w")
utc_label_text.pack(side=tk.LEFT, padx=5)

# Etykieta zegara
utc_label = tk.Label(utc_frame, font=("Helvetica", 14), anchor="w")  # Etykieta zegara w ramce
utc_label.pack(side=tk.LEFT)

# Uruchomienie zegara UTC
update_utc_clock(utc_label)

# Zwiększenie szerokości i wysokości pól formularza oraz ustawienie odstępów
entry_width = 30  # Nowa szerokość pól wejściowych (1,5x)
entry_font = ("Helvetica", 15)  # Zwiększona czcionka (dla większej wysokości)
spacing = 10  # Odstęp między polami (10px)

tk.Label(form_frame, text="Znak wywoławczy").grid(row=0, column=0, padx=spacing, pady=spacing)
callsign_entry = tk.Entry(form_frame, width=entry_width, font=entry_font)
callsign_entry.grid(row=0, column=1, padx=spacing, pady=spacing)

tk.Label(form_frame, text="RST wysłane").grid(row=1, column=0, padx=spacing, pady=spacing)
rst_sent_entry = tk.Entry(form_frame, width=entry_width, font=entry_font)
rst_sent_entry.grid(row=1, column=1, padx=spacing, pady=spacing)
rst_sent_entry.insert(0, "59")  # Domyślna wartość

tk.Label(form_frame, text="RST odebrane").grid(row=2, column=0, padx=spacing, pady=spacing)
rst_received_entry = tk.Entry(form_frame, width=entry_width, font=entry_font)
rst_received_entry.grid(row=2, column=1, padx=spacing, pady=spacing)
rst_received_entry.insert(0, "59")  # Domyślna wartość

tk.Label(form_frame, text="Pasmo").grid(row=0, column=2, padx=spacing, pady=spacing)
band_combobox = ttk.Combobox(form_frame, values=["160m", "80m", "40m", "30m", "20m", "17m", "15m", "12m", "10m", "6m", "4m", "2m", "70cm"], state="readonly", width=entry_width, font=entry_font)
band_combobox.grid(row=0, column=3, padx=spacing, pady=spacing)

tk.Label(form_frame, text="Tryb").grid(row=1, column=2, padx=spacing, pady=spacing)
mode_combobox = ttk.Combobox(form_frame, values=["SSB", "CW", "DIGI", "FM"], state="readonly", width=entry_width, font=entry_font)
mode_combobox.grid(row=1, column=3, padx=spacing, pady=spacing)

tk.Label(form_frame, text="Moc (W)").grid(row=2, column=2, padx=spacing, pady=spacing)
power_entry = tk.Entry(form_frame, width=entry_width, font=entry_font)
power_entry.grid(row=2, column=3, padx=spacing, pady=spacing)

tk.Label(form_frame, text="Imię").grid(row=0, column=4, padx=spacing, pady=spacing)
name_entry = tk.Entry(form_frame, width=entry_width, font=entry_font)
name_entry.grid(row=0, column=5, padx=spacing, pady=spacing)

tk.Label(form_frame, text="Kraj").grid(row=1, column=4, padx=spacing, pady=spacing)
country_entry = tk.Entry(form_frame, width=entry_width, font=entry_font)
country_entry.grid(row=1, column=5, padx=spacing, pady=spacing)

tk.Label(form_frame, text="Grid Square").grid(row=2, column=4, padx=spacing, pady=spacing)
grid_square_entry = tk.Entry(form_frame, width=entry_width, font=entry_font)
grid_square_entry.grid(row=2, column=5, padx=spacing, pady=spacing)

tk.Label(form_frame, text="Komentarz").grid(row=3, column=4, padx=spacing, pady=spacing)
comment_entry = tk.Entry(form_frame, width=entry_width, font=entry_font)
comment_entry.grid(row=3, column=5, padx=spacing, pady=spacing)

tk.Button(form_frame, text="Dodaj QSO", command=add_entry).grid(row=4, column=0, columnspan=2, pady=10)
#tk.Button(form_frame, text="Auto-wypełnianie z QRZ", command=auto_fill_qrz).grid(row=4, column=4, columnspan=2, pady=10)
tk.Button(form_frame, text="Usuń QSO", command=delete_entry).grid(row=4, column=6, columnspan=2, pady=10)

# Dolna sekcja - tabela
table_frame = tk.Frame(root, padx=10, pady=10)
table_frame.pack(fill=tk.BOTH, expand=True)

# Dodanie przycisku "Usuń QSO" do lewego górnego rogu nad tabelą
delete_button_frame = tk.Frame(table_frame)
delete_button_frame.pack(fill=tk.X, pady=10)

tk.Button(delete_button_frame, text="Usuń QSO", command=delete_entry).pack(side=tk.RIGHT)

# Tabela
columns = ("date_time", "callsign", "rst_sent", "rst_received", "band", "mode", "power", "grid_square", "distance", "name", "country", "comment")
table = ttk.Treeview(table_frame, columns=columns, show="headings")

# Ustawienia dla oddzielenia kolumn
style = ttk.Style()
style.configure("Treeview.Heading", padding=[5, 10])  # Ustawienie paddingu w nagłówkach
style.configure("Treeview", rowheight=30)  # Zwiększenie wysokości wiersza

# Dodanie cienkich linii oddzielających kolumny przez kolorowanie tła i obramowań
style.configure("Treeview", 
                background="#2e2e2e",  # Tło tabeli (ciemne)
                foreground="white",  # Kolor tekstu (biały)
                fieldbackground="#2e2e2e",  # Tło pól komórek (ciemne)
                borderwidth=5)  # Dodanie cienkich obramowań dla komórek

style.configure("Treeview.Heading",
                background="#444444",  # Ciemne tło nagłówków
                foreground="white",  # Kolor tekstu nagłówków
                font=("Helvetica", 10, "bold"),
                padding=[10, 5])

# Dodatkowe ustawienia, które mogą pomóc uzyskać wrażenie oddzielonych kolumn
style.map("Treeview",
          background=[('selected', '#555555')],  # Kolor zaznaczonego wiersza
          foreground=[('selected', 'white')])

# Nagłówki tabeli
for col in columns:
    table.heading(col, text=col.replace("_", " ").capitalize())
    table.column(col, width=120, anchor="center", minwidth=80)  # Szerokość kolumn

table.pack(fill=tk.BOTH, expand=True)

# Inicjalizacja
db.initialize_database()
db.update_table()

root.mainloop()


