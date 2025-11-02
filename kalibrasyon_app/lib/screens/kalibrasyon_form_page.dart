import 'package:flutter/material.dart';
import 'package:record/record.dart';
import 'dart:html' as html;
import 'package:http/http.dart' as http;
import 'dart:convert';

class KalibrasyonFormPage extends StatefulWidget {
  @override
  _KalibrasyonFormPageState createState() => _KalibrasyonFormPageState();
}

class _KalibrasyonFormPageState extends State<KalibrasyonFormPage> {
  final _formKey = GlobalKey<FormState>();
  final _sicaklikController = TextEditingController();
  final _nemController = TextEditingController();
  
  // Ses kaydı
  final AudioRecorder _record = AudioRecorder();
  bool _isRecording = false;
  String? _audioPath;
  List<String> _fotograflar = [];
  Map<String, dynamic> cihaz = {};
  
  // Kumpas için örnek ölçüm noktaları
  final List<Map<String, dynamic>> _olcumNoktalari = [
    {'nominal': 0, 'olculen': null, 'sapma': 0, 'belirsizlik': 0.01, 'sonuc': null},
    {'nominal': 25, 'olculen': null, 'sapma': 0, 'belirsizlik': 0.01, 'sonuc': null},
    {'nominal': 50, 'olculen': null, 'sapma': 0, 'belirsizlik': 0.01, 'sonuc': null},
    {'nominal': 75, 'olculen': null, 'sapma': 0, 'belirsizlik': 0.01, 'sonuc': null},
    {'nominal': 100, 'olculen': null, 'sapma': 0, 'belirsizlik': 0.01, 'sonuc': null},
  ];

  @override
  Widget build(BuildContext context) {
    final arguments = ModalRoute.of(context)?.settings.arguments;
    cihaz = arguments != null 
        ? arguments as Map<String, dynamic>
        : {
            'id': 0,
            'kod': 'TEST-001',
            'ad': 'Test Cihazı',
            'tip': 'kumpas',
            'marka': 'Test Marka',
            'model': 'Test Model',
          };
    
    return Scaffold(
      appBar: AppBar(
        title: Text('Kalibrasyon: ${cihaz['kod']}'),
        backgroundColor: Colors.blue.shade700,
        actions: [
          IconButton(
            icon: Icon(Icons.save),
            onPressed: _kaydet,
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: SingleChildScrollView(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildCihazBilgileri(cihaz),
              SizedBox(height: 24),
              _buildOrtamKosullari(),
              SizedBox(height: 24),
              _buildOlcumTablosu(),
              SizedBox(height: 24),
              _buildEkler(),
              SizedBox(height: 24),
              _buildSesliOzet(),
              SizedBox(height: 32),
              _buildKaydetButon(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCihazBilgileri(Map<String, dynamic> cihaz) {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Cihaz Bilgileri',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            Divider(),
            _InfoRow('Cihaz', '${cihaz['ad']} (${cihaz['kod']})'),
            _InfoRow('Marka/Model', '${cihaz['marka']} ${cihaz['model']}'),
            _InfoRow('Seri No', '12345678'),
            _InfoRow('Ölçüm Aralığı', '0-150mm'),
            _InfoRow('Çözünürlük', '0.01mm'),
          ],
        ),
      ),
    );
  }

  Widget _buildOrtamKosullari() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Ortam Koşulları',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            Divider(),
            Row(
              children: [
                Expanded(
                  child: TextFormField(
                    controller: _sicaklikController,
                    decoration: InputDecoration(
                      labelText: 'Sıcaklık (°C)',
                      border: OutlineInputBorder(),
                      suffixText: '°C',
                    ),
                    keyboardType: TextInputType.number,
                    validator: (value) {
                      if (value?.isEmpty ?? true) return 'Zorunlu alan';
                      return null;
                    },
                  ),
                ),
                SizedBox(width: 16),
                Expanded(
                  child: TextFormField(
                    controller: _nemController,
                    decoration: InputDecoration(
                      labelText: 'Nem (%)',
                      border: OutlineInputBorder(),
                      suffixText: '%',
                    ),
                    keyboardType: TextInputType.number,
                    validator: (value) {
                      if (value?.isEmpty ?? true) return 'Zorunlu alan';
                      return null;
                    },
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildOlcumTablosu() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Ölçüm Sonuçları',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            Divider(),
            SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                columns: [
                  DataColumn(label: Text('Nominal\n(mm)')),
                  DataColumn(label: Text('Ölçülen\n(mm)')),
                  DataColumn(label: Text('Sapma\n(mm)')),
                  DataColumn(label: Text('Belirsizlik\n(mm)')),
                  DataColumn(label: Text('Sonuç')),
                ],
                rows: _olcumNoktalari.map((nokta) {
                  return DataRow(
                    cells: [
                      DataCell(Text(nokta['nominal'].toString())),
                      DataCell(
                        TextFormField(
                          decoration: InputDecoration(
                            border: InputBorder.none,
                            hintText: '...',
                          ),
                          keyboardType: TextInputType.number,
                          onChanged: (value) {
                            setState(() {
                              if (value.isNotEmpty) {
                                double olculen = double.parse(value);
                                nokta['olculen'] = olculen;
                                nokta['sapma'] = olculen - nokta['nominal'];
                                nokta['sonuc'] = nokta['sapma'].abs() <= 0.05;
                              }
                            });
                          },
                        ),
                      ),
                      DataCell(Text(
                        nokta['sapma']?.toStringAsFixed(3) ?? '-',
                        style: TextStyle(
                          color: (nokta['sapma']?.abs() ?? 0) > 0.05 
                              ? Colors.red 
                              : Colors.green,
                        ),
                      )),
                      DataCell(Text(nokta['belirsizlik'].toString())),
                      DataCell(
                        nokta['sonuc'] == null
                            ? Text('-')
                            : Icon(
                                nokta['sonuc'] ? Icons.check : Icons.close,
                                color: nokta['sonuc'] ? Colors.green : Colors.red,
                              ),
                      ),
                    ],
                  );
                }).toList(),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEkler() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Ekler',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            Divider(),
            Row(
              children: [
                ElevatedButton.icon(
                  onPressed: _fotografEkle,
                  icon: Icon(Icons.camera_alt),
                  label: Text('Fotoğraf Ekle'),
                ),
                SizedBox(width: 16),
                ElevatedButton.icon(
                  onPressed: _dosyaEkle,
                  icon: Icon(Icons.attach_file),
                  label: Text('Dosya Ekle'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSesliOzet() {
    return Card(
      color: Colors.orange.shade50,
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(Icons.mic, color: Colors.orange),
                SizedBox(width: 8),
                Text(
                  'Sesli Özet',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
                ),
              ],
            ),
            Divider(),
            Text(
              'Kalibrasyonla ilgili notlarınızı sesli olarak kaydedin:',
              style: TextStyle(color: Colors.grey.shade700),
            ),
            SizedBox(height: 8),
            Text(
              '• Cihazın genel durumu\n'
              '• Görünür hasar veya aşınma\n'
              '• Müşteri gözlemleri\n'
              '• Öneriler',
              style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
            ),
            SizedBox(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton.icon(
                  onPressed: _toggleRecording,
                  icon: Icon(_isRecording ? Icons.stop : Icons.mic),
                  label: Text(_isRecording ? 'Kaydı Durdur' : 'Kayda Başla'),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: _isRecording ? Colors.red : Colors.orange,
                    foregroundColor: Colors.white,
                    padding: EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                  ),
                ),
                if (_audioPath != null) ...[
                  SizedBox(width: 16),
                  IconButton(
                    icon: Icon(Icons.play_circle, size: 32, color: Colors.green),
                    onPressed: _playRecording,
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildKaydetButon() {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        onPressed: _kaydet,
        child: Text('Kalibrasyonu Kaydet'),
        style: ElevatedButton.styleFrom(
          padding: EdgeInsets.symmetric(vertical: 16),
          backgroundColor: Colors.green,
          foregroundColor: Colors.white,
        ),
      ),
    );
  }

  Widget _InfoRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.grey.shade700)),
          Text(value, style: TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  void _fotografEkle() {
    final input = html.FileUploadInputElement()..accept = 'image/*';
    input.click();
    input.onChange.listen((e) {
      final files = input.files;
      if (files?.isNotEmpty ?? false) {
        final file = files!.first;
        // Fotoğraf yükleme işlemi
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fotoğraf eklendi: ${file.name}')),
        );
      }
    });
  }

  void _dosyaEkle() {
    final input = html.FileUploadInputElement();
    input.click();
    input.onChange.listen((e) {
      final files = input.files;
      if (files?.isNotEmpty ?? false) {
        final file = files!.first;
        // Dosya yükleme işlemi
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Dosya eklendi: ${file.name}')),
        );
      }
    });
  }

  void _toggleRecording() async {
    if (_isRecording) {
      // Kaydı durdur
      String? path = await _record.stop();
      setState(() {
        _isRecording = false;
        _audioPath = path;
      });
    } else {
      // Kayda başla
      if (await _record.hasPermission()) {
        await _record.start(
          RecordConfig(
            encoder: AudioEncoder.wav,
            sampleRate: 16000,
          ),
          path: 'audio_${DateTime.now().millisecondsSinceEpoch}.wav',
        );
        setState(() {
          _isRecording = true;
        });
      }
    }
  }

  void _playRecording() {
    // Ses dosyasını oynat
    if (_audioPath != null) {
      // Web'de ses oynatma
    }
  }

  void _kaydet() async {
    if (_formKey.currentState!.validate()) {
      // Ölçüm verilerini topla
      Map<String, dynamic> kalibrasyonData = {
        'cihaz_id': cihaz['id'] ?? 0,
        'cihaz_kodu': cihaz['kod'] ?? 'TEST-001',
        'cihaz_adi': cihaz['ad'] ?? 'Test Cihazı',
        'ortam': {
          'sicaklik': double.tryParse(_sicaklikController.text) ?? 23.0,
          'nem': double.tryParse(_nemController.text) ?? 50.0,
        },
        'olcumler': _olcumNoktalari.where((nokta) => nokta['olculen'] != null).toList(),
        'sesli_ozet': _audioPath,
        'fotograflar': _fotograflar,
        'tarih': DateTime.now().toIso8601String(),
        'teknisyen': 'Test Teknisyen',
      };
      
      print('Frontend: Kalibrasyon verisi gönderiliyor...');
      
      // Kaydedilen verileri göster
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Text('Kalibrasyon Kaydedildi!'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('Cihaz: ${kalibrasyonData['cihaz_kodu']} - ${kalibrasyonData['cihaz_adi']}'),
                Text('Sıcaklık: ${kalibrasyonData['ortam']['sicaklik']}°C'),
                Text('Nem: ${kalibrasyonData['ortam']['nem']}%'),
                Text('Girilen Ölçüm: ${kalibrasyonData['olcumler'].length} adet'),
                SizedBox(height: 16),
                Text('Ölçüm Sonuçları:', style: TextStyle(fontWeight: FontWeight.bold)),
                ...kalibrasyonData['olcumler'].map((olcum) => Text(
                  '${olcum['nominal']} mm → ${olcum['olculen']} mm (Sapma: ${olcum['sapma'].toStringAsFixed(3)})',
                  style: TextStyle(
                    color: olcum['sapma'].abs() <= olcum['belirsizlik'] ? Colors.green : Colors.red,
                  ),
                )),
              ],
            ),
          ),
          actions: [
            TextButton(
              onPressed: () {
                Navigator.pop(context);
                Navigator.pop(context);
              },
              child: Text('Tamam'),
            ),
          ],
        ),
      );
      
      // Backend'e gönder
      try {
        final response = await http.post(
          Uri.parse('http://localhost:8000/api/kalibrasyonlar'),
          headers: {'Content-Type': 'application/json'},
          body: json.encode({
            'organizasyon_id': 3,  // Son oluşturulan organizasyon
            'cihaz_id': 1,  // Mevcut cihaz DK-001
            'ortam': {
              'sicaklik': double.tryParse(_sicaklikController.text) ?? 23.0,
              'nem': double.tryParse(_nemController.text) ?? 50.0,
            },
            'olcumler': _olcumNoktalari.where((nokta) => nokta['olculen'] != null).toList(),
            'sesli_ozet': _audioPath ?? '',
            'fotograflar': _fotograflar,
            'teknisyen': 'Test Teknisyen',
            'cihaz_adi': cihaz['ad'],
            'marka': cihaz['marka'],
            'model': cihaz['model'],
            'seri_no': cihaz['seri_no'] ?? '',
          }),
        );
        
        if (response.statusCode == 200) {
          final result = json.decode(response.body);
          print('Kalibrasyon kaydedildi! ID: ${result['id']}');
        } else {
          print('Backend hatası: ${response.body}');
        }
      } catch (e) {
        print('Bağlantı hatası: $e');
      }
    }
  }
}
