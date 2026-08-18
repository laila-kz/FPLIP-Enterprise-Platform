📊 Measuring endpoint latency...
============================================================

🔍 Testing: /oee/daily
   Params: {'start_date': '2026-08-01', 'end_date': '2026-08-08'}
   Cache-cold: 4.447s
   Cache-warm: 0.017s
   Speedup: 263.2x
   Status: 200
   Response size: 2 chars

🔍 Testing: /oee/summary
   Params: {'start_date': '2026-08-01', 'end_date': '2026-08-08'}
   Cache-cold: 1.619s
   Cache-warm: 0.017s
   Speedup: 94.3x
   Status: 200
   Response size: 2 chars

🔍 Testing: /scrap/root-cause
   Params: {'start_date': '2026-08-01', 'end_date': '2026-08-08'}
   Cache-cold: 1.624s
   Cache-warm: 0.008s
   Speedup: 192.1x
   Status: 200
   Response size: 2 chars

============================================================
📊 SUMMARY
============================================================
Endpoint                  Cold (s)   Warm (s)   Speedup   
------------------------------------------------------------
/oee/daily                4.447      0.017      263.2     x
/oee/summary              1.619      0.017      94.3      x
/scrap/root-cause         1.624      0.008      192.1     x