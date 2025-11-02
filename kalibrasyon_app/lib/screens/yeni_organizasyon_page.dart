import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class YeniOrganizasyonPage extends StatefulWidget {
  @override
  _YeniOrganizasyonPageState createState() => _YeniOrganizasyonPageState();
}

class _YeniOrganizasyonPageState extends State<YeniOrganizasyonPage> {
  final _formKey = GlobalKey<FormState>();
  final _adController = TextEditingController();
  final _musteriController = TextEditingController();
  final _adresController = TextEditingController();
  final _notlarController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Yeni Organizasyon'),
        backgroundColor: Colors.blue.shade700,
      ),
      body: Form(
        key: _formKey,
        child: SingleChildScrollView(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Card(
                child: Padding(
                  padding: EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Organizasyon Bilgileri',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      SizedBox(height: 16),
                      TextFormField(
                        controller: _adController,
                        decoration: InputDecoration(
                          labelText: 'Organizasyon Adı',
                          hintText: 'Örn: Ocak 2024 - ABC Fabrika Kalibrasyonları',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.business_center),
                        ),
                        validator: (value) {
                          if (value?.isEmpty ?? true) {
                            return 'Bu alan zorunludur';
                          }
                          return null;
                        },
                      ),
                      SizedBox(height: 16),
                      TextFormField(
                        controller: _musteriController,
                        decoration: InputDecoration(
                          labelText: 'Müşteri Adı',
                          hintText: 'Örn: ABC Plastik San. Tic. Ltd.',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.business),
                        ),
                        validator: (value) {
                          if (value?.isEmpty ?? true) {
                            return 'Bu alan zorunludur';
                          }
                          return null;
                        },
                      ),
                      SizedBox(height: 16),
                      TextFormField(
                        controller: _adresController,
                        decoration: InputDecoration(
                          labelText: 'Müşteri Adresi',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.location_on),
                        ),
                        maxLines: 2,
                      ),
                      SizedBox(height: 16),
                      TextFormField(
                        controller: _notlarController,
                        decoration: InputDecoration(
                          labelText: 'Notlar (Opsiyonel)',
                          border: OutlineInputBorder(),
                          prefixIcon: Icon(Icons.note),
                        ),
                        maxLines: 3,
                      ),
                    ],
                  ),
                ),
              ),
              SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 50,
                child: ElevatedButton(
                  onPressed: _organizasyonOlustur,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blue.shade700,
                    foregroundColor: Colors.white,
                  ),
                  child: Text(
                    'Organizasyon Oluştur',
                    style: TextStyle(fontSize: 16),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  void _organizasyonOlustur() async {
    if (_formKey.currentState!.validate()) {
      // Backend'e kaydet
      try {
        final response = await http.post(
          Uri.parse('http://localhost:8000/api/organizasyonlar'),
          headers: {'Content-Type': 'application/json'},
          body: json.encode({
            'ad': _adController.text,
            'musteri_adi': _musteriController.text,
            'musteri_adres': _adresController.text,
            'notlar': _notlarController.text,
            'created_by': 'frontend_user',
          }),
        );
        
        if (response.statusCode == 200) {
          final result = json.decode(response.body);
          
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Organizasyon başarıyla oluşturuldu! (ID: ${result['id']})'),
              backgroundColor: Colors.green,
              duration: Duration(seconds: 2),
            ),
          );
          
          // Organizasyon listesine geri dön
          Navigator.pop(context);
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Hata: ${response.statusCode}'),
              backgroundColor: Colors.red,
            ),
          );
        }
      } catch (e) {
        print('Organizasyon oluşturma hatası: $e');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Bağlantı hatası: Backend çalışmıyor olabilir'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  void dispose() {
    _adController.dispose();
    _musteriController.dispose();
    _adresController.dispose();
    _notlarController.dispose();
    super.dispose();
  }
}
