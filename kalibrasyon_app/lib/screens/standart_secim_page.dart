import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class StandartSecimPage extends StatefulWidget {
  final Map<String, dynamic> cihaz;
  
  const StandartSecimPage({Key? key, required this.cihaz}) : super(key: key);
  
  @override
  _StandartSecimPageState createState() => _StandartSecimPageState();
}

class _StandartSecimPageState extends State<StandartSecimPage> {
  List<Map<String, dynamic>> _standartlar = [];
  bool _isLoading = true;
  int? _secilenStandartId;
  int? _secilenSablonId;

  @override
  void initState() {
    super.initState();
    _loadStandartlar();
  }

  Future<void> _loadStandartlar() async {
    try {
      // Cihaz tipine göre uygun standartları getir
      final cihazTipi = widget.cihaz['tip'] ?? 'kumpas';
      final response = await http.get(
        Uri.parse('http://localhost:8000/api/standards/$cihazTipi'),
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _standartlar = List<Map<String, dynamic>>.from(data['standartlar']);
          _isLoading = false;
        });
      }
    } catch (e) {
      print('Standart yükleme hatası: $e');
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Kalibrasyon Standardı Seçin'),
        backgroundColor: Colors.blue.shade700,
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : Column(
              children: [
                // Cihaz Bilgisi
                Container(
                  padding: EdgeInsets.all(16),
                  color: Colors.blue.shade50,
                  width: double.infinity,
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Seçilen Cihaz',
                        style: TextStyle(
                          fontSize: 12,
                          color: Colors.grey.shade700,
                        ),
                      ),
                      SizedBox(height: 4),
                      Text(
                        '${widget.cihaz['kod']} - ${widget.cihaz['ad']}',
                        style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Text(
                        '${widget.cihaz['marka']} ${widget.cihaz['model']}',
                        style: TextStyle(color: Colors.grey.shade600),
                      ),
                    ],
                  ),
                ),
                
                // Standart Listesi
                Expanded(
                  child: _standartlar.isEmpty
                      ? Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.warning, size: 64, color: Colors.orange),
                              SizedBox(height: 16),
                              Text('Bu cihaz tipi için standart bulunamadı'),
                            ],
                          ),
                        )
                      : ListView.builder(
                          padding: EdgeInsets.all(16),
                          itemCount: _standartlar.length,
                          itemBuilder: (context, index) {
                            final standart = _standartlar[index];
                            bool isSelected = _secilenStandartId == standart['id'];
                            
                            return Card(
                              margin: EdgeInsets.only(bottom: 12),
                              color: isSelected ? Colors.blue.shade50 : Colors.white,
                              elevation: isSelected ? 4 : 1,
                              child: RadioListTile<int>(
                                value: standart['id'],
                                groupValue: _secilenStandartId,
                                onChanged: (value) {
                                  setState(() {
                                    _secilenStandartId = value;
                                    _secilenSablonId = standart['sablon_id'];
                                  });
                                },
                                title: Text(
                                  standart['standart_kod'],
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 16,
                                  ),
                                ),
                                subtitle: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    SizedBox(height: 4),
                                    Text(standart['standart_ad']),
                                    SizedBox(height: 4),
                                    Row(
                                      children: [
                                        Icon(Icons.category, size: 14, color: Colors.grey),
                                        SizedBox(width: 4),
                                        Text(
                                          standart['grup'],
                                          style: TextStyle(fontSize: 12),
                                        ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                        ),
                ),
                
                // Devam Butonu
                Container(
                  padding: EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    boxShadow: [
                      BoxShadow(
                        color: Colors.grey.shade300,
                        blurRadius: 4,
                        offset: Offset(0, -2),
                      ),
                    ],
                  ),
                  child: SizedBox(
                    width: double.infinity,
                    height: 50,
                    child: ElevatedButton(
                      onPressed: _secilenStandartId != null ? _devamEt : null,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: Colors.blue.shade700,
                        foregroundColor: Colors.white,
                        disabledBackgroundColor: Colors.grey.shade300,
                      ),
                      child: Text(
                        'Standart ile Devam Et',
                        style: TextStyle(fontSize: 16),
                      ),
                    ),
                  ),
                ),
              ],
            ),
    );
  }

  void _devamEt() async {
    if (_secilenSablonId == null) return;
    
    // Parametreleri yükle
    try {
      final response = await http.get(
        Uri.parse('http://localhost:8000/api/templates/$_secilenSablonId/parameters'),
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        
        // Kalibrasyon formuna git
        Navigator.pushReplacementNamed(
          context,
          '/kalibrasyon-form',
          arguments: {
            ...widget.cihaz,
            'standart_id': _secilenStandartId,
            'sablon_id': _secilenSablonId,
            'parametreler': data['parametreler'],
          },
        );
      }
    } catch (e) {
      print('Parametre yükleme hatası: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Parametreler yüklenemedi'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }
}
