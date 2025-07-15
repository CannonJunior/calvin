#!/usr/bin/env python3
import psycopg2

try:
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='calvin_earnings',
        user='calvin_user',
        password='calvin_pass'
    )
    cursor = conn.cursor()
    
    # Delete all earnings data except AAPL  
    cursor.execute("DELETE FROM earnings WHERE symbol != 'AAPL'")
    deleted_count = cursor.rowcount
    
    conn.commit()
    print(f'Deleted {deleted_count} non-AAPL earnings records')
    
    # Verify remaining data
    cursor.execute('SELECT symbol, COUNT(*) as count FROM earnings GROUP BY symbol ORDER BY symbol')
    results = cursor.fetchall()
    
    print('Remaining earnings data:')
    for row in results:
        print(f'  {row[0]}: {row[1]} records')
    
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f'Error: {e}')