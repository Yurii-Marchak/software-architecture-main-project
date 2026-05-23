import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def analyze_database():
    print("Підключення до бази даних pc_warehouse...\n")
    client = AsyncIOMotorClient('mongodb://localhost:27017/')
    db = client['pc_warehouse']
    
    collections = ['CPU', 'Motherboard', 'Memory', 'GPU', 'Case', 'Cooler', 'Storage', 'PSU']
    

    exclude_fields = {'_id', 'id', 'name', 'image', 'url', 'price', 'stock'}
    
    for coll_name in collections:
        print("=" * 60)
        print(f" АНАЛІЗ КОЛЕКЦІЇ: {coll_name} ".center(60, "="))
        print("=" * 60)
        
        collection = db[coll_name]
        docs = await collection.find({}).to_list(length=None)
        
        if not docs:
            print("Колекція порожня!\n")
            continue
            

        all_keys = set()
        for doc in docs:
            all_keys.update(doc.keys())
            

        keys_to_analyze = all_keys - exclude_fields
        
        for key in keys_to_analyze:
            unique_vals = set()
            for doc in docs:
                if key in doc and doc[key] is not None:
                    unique_vals.add(doc[key])
            

            if len(unique_vals) < 50:
                print(f"Поле '{key}' можна фільтрувати (унікальних значень: {len(unique_vals)}).")

                try:
                    sorted_vals = sorted(list(unique_vals))
                except TypeError:

                    sorted_vals = sorted(list(unique_vals), key=str)
                    
                print(f"   Значення: {sorted_vals}\n")
            else:
                print(f"Поле '{key}' має забагато унікальних значень ({len(unique_vals)}).")
                print(f"   Краще використати діапазон (від - до), а не галочки.\n")

if __name__ == '__main__':
    asyncio.run(analyze_database())