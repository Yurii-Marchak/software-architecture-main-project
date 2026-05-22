import pandas as pd
import re
import random
import itertools
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

# Функція для обробки колекції Memory
def parse_memory_name(row):
    name = str(row.get('name', ''))
    # Патерн: шукаємо блок, наприклад: (2 x 8 GB) DDR3-1600 CL9
    pattern = r'\s*\((?P<sticks>\d+\s*x\s*\d+\s*GB)\)\s+(?P<type>DDR[345])-(?P<freq>\d+)\s+(?P<cas>CL\d+)\s*'
    match = re.search(pattern, name)
    
    if match:
        row['size'] = f"({match.group('sticks')})" # перезаписуємо size (кількість і об'єм)
        row['type'] = match.group('type') # виокремлюємо тип
        row['frequency'] = int(match.group('freq')) # виокремлюємо частоту
        row['CAS_latency'] = match.group('cas') # виокремлюємо таймінги
        
        # Видаляємо знайдений блок з оригінального імені
        new_name = name.replace(match.group(0), ' ')
        # Видаляємо зайві пробіли
        row['name'] = re.sub(r'\s+', ' ', new_name).strip()
    else:
        row['frequency'] = None
        row['CAS_latency'] = None
    
    return row

async def main():
    print("Початок підготовки даних та міграції у MongoDB...")
    
    # Підключення до MongoDB (переконайтеся, що локальний сервер працює)
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client['pc_warehouse'] # Назва бази даних проекту
    
    collections = ['Case', 'Cooler', 'CPU', 'GPU', 'Memory', 'Motherboard', 'PSU', 'Storage']
    
    # 1. Завантажуємо CPU для отримання унікальних сокетів
    try:
        cpu_df = pd.read_csv('CPU.csv')
    except FileNotFoundError:
        print("Помилка: Файли CSV не знайдено. Помістіть їх у ту ж папку, що й скрипт.")
        return

    unique_sockets = cpu_df['socket'].dropna().unique().tolist()
    
    dfs = {}
    for coll in collections:
        dfs[coll] = pd.read_csv(f'{coll}.csv')
        
    # --- 1. Обробка Cooler ---
    print("Обробка колекції Cooler...")
    # Розподіляємо унікальні сокети в рівній пропорції
    socket_cycle = itertools.cycle(unique_sockets)
    dfs['Cooler']['socket'] = [next(socket_cycle) for _ in range(len(dfs['Cooler']))]
    
    # --- 2. Обробка Motherboard ---
    print("Обробка колекції Motherboard...")
    dfs['Motherboard']['supported_memory_type'] = [random.choice(['DDR3', 'DDR4', 'DDR5']) for _ in range(len(dfs['Motherboard']))]
    dfs['Motherboard']['max_memory_sticks'] = [random.choice([2, 4, 6, 8]) for _ in range(len(dfs['Motherboard']))]
    
    # --- 3. Обробка Memory ---
    print("Обробка колекції Memory...")
    dfs['Memory'] = dfs['Memory'].apply(parse_memory_name, axis=1)
    
    # --- 4. Додавання ціни та кількості до всіх колекцій ---
    print("Генерація ціни та кількості на складі...")
    for coll in collections:
        dfs[coll]['price'] = [random.randint(100, 500) for _ in range(len(dfs[coll]))]
        dfs[coll]['stock'] = [random.randint(5, 20) for _ in range(len(dfs[coll]))]
    
    # --- 5. Вставка у MongoDB ---
    print("Вставка даних у MongoDB...")
    for coll in collections:
        records = dfs[coll].to_dict(orient='records')
        if records:
            # Очищуємо колекцію перед вставкою, щоб не дублювати дані при повторних запусках
            await db[coll].delete_many({})
            await db[coll].insert_many(records)
            print(f" -> Колекція {coll}: успішно додано {len(records)} записів.")
            
    print("Міграція успішно завершена! База даних готова.")
    from datetime import datetime

    # --- 6. Ініціалізація додаткових колекцій (Users, Orders, PC_Builds) ---
    print("Ініціалізація колекцій users, orders, pc_builds...")
    
    # Очищення колекцій перед заповненням (щоб не було дублікатів при повторних запусках)
    await db['users'].delete_many({})
    await db['orders'].delete_many({})
    await db['pc_builds'].delete_many({})
    
    # 6.1. Тестовий користувач (відповідно до вимог)
    test_user = {
        "email": "client@example.com",
        "first_name": "Іван",
        "last_name": "Іванов",
        "phone": "+380991234567",
        "order_ids": ["order_001"] # Зв'язок з чеком
    }
    await db['users'].insert_one(test_user)
    
    # 6.2. Тестовий чек/замовлення (відповідно до вимог)
    test_order = {
        "_id": "order_001",
        "email": "client@example.com", # ДОДАНО: обов'язкове поле
        "items": [
            {"name": "AMD Ryzen 5 5600X", "price": 250, "quantity": 1}, # ДОДАНО: quantity
            {"name": "Corsair Vengeance 16 GB", "price": 80, "quantity": 1} # ДОДАНО: quantity
        ],
        "total_price": 330,
        "date": datetime.now()
    }
    await db['orders'].insert_one(test_order)
    
    # 6.3. Тестова готова конфігурація ПК (відповідно до вимог)
    test_build = {
        "name": "Budget Gaming Build 2024", # Унікальна назва збірки
        "components": {
            "CPU": "AMD Ryzen 5 5600X",
            "Motherboard": "MSI B550 TOMAHAWK",
            "Memory": "Corsair Vengeance 16 GB",
            "Storage": "Samsung 970 Evo Plus 1TB",
            "Cooler": "Cooler Master Hyper 212",
            "GPU": "NVIDIA GeForce RTX 3060",
            "Case": "NZXT H510",
            "PSU": "Corsair RM750x"
        }
    }
    await db['pc_builds'].insert_one(test_build)
    
    print("Додаткові колекції (users, orders, pc_builds) успішно ініціалізовано!")
if __name__ == '__main__':
    asyncio.run(main())
