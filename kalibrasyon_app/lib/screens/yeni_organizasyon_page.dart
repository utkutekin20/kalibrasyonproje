import 'package:flutter/material.dart';

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

  void _organizasyonOlustur() {
    if (_formKey.currentState!.validate()) {
      // TODO: Backend'e kaydet
      
      // Şimdilik sadece başarı mesajı göster
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Organizasyon oluşturuldu!'),
          backgroundColor: Colors.green,
        ),
      );
      
      // Organizasyon detay sayfasına git
      Navigator.pushReplacementNamed(
        context,
        '/organizasyon-detay',
        arguments: {
          'id': DateTime.now().millisecondsSinceEpoch,
          'ad': _adController.text,
          'musteri': _musteriController.text,
          'baslangic': DateTime.now(),
          'durum': 'devam_ediyor',
          'cihaz_sayisi': 0,
          'tamamlanan': 0,
        },
      );
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
