import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class OrganizasyonDetayPage extends StatefulWidget {
  @override
  _OrganizasyonDetayPageState createState() => _OrganizasyonDetayPageState();
}

class _OrganizasyonDetayPageState extends State<OrganizasyonDetayPage> {
  int _selectedTab = 0;

  @override
  Widget build(BuildContext context) {
    final arguments = ModalRoute.of(context)?.settings.arguments;
    final org = arguments != null 
        ? arguments as Map<String, dynamic>
        : {
            'id': 0,
            'ad': 'Test Organizasyon',
            'musteri': 'Test Müşteri',
            'baslangic': DateTime.now(),
            'durum': 'devam_ediyor',
            'cihaz_sayisi': 0,
            'tamamlanan': 0,
          };

    return Scaffold(
      appBar: AppBar(
        title: Text(org['ad']),
        backgroundColor: Colors.blue.shade700,
        actions: [
          IconButton(
            icon: Icon(Icons.more_vert),
            onPressed: () {},
          ),
        ],
      ),
      body: Column(
        children: [
          _buildHeader(org),
          _buildTabs(),
          Expanded(
            child: _buildTabContent(),
          ),
        ],
      ),
    );
  }

  Widget _buildHeader(Map<String, dynamic> org) {
    return Container(
      padding: EdgeInsets.all(16),
      color: Colors.grey.shade100,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            org['musteri'] ?? 'Müşteri Adı',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          SizedBox(height: 8),
          Row(
            children: [
              Icon(Icons.calendar_today, size: 16, color: Colors.grey),
              SizedBox(width: 4),
              Text(
                'Başlangıç: ${DateFormat('dd.MM.yyyy').format(org['baslangic'])}',
                style: TextStyle(color: Colors.grey),
              ),
              SizedBox(width: 16),
              _durumChip(org['durum']),
            ],
          ),
        ],
      ),
    );
  }

  Widget _durumChip(String durum) {
    Color color;
    String text;
    IconData icon;

    switch (durum) {
      case 'devam_ediyor':
        color = Colors.orange;
        text = 'Devam Ediyor';
        icon = Icons.access_time;
        break;
      case 'tamamlandi':
        color = Colors.green;
        text = 'Tamamlandı';
        icon = Icons.check_circle;
        break;
      default:
        color = Colors.grey;
        text = 'Bilinmiyor';
        icon = Icons.help;
    }

    return Chip(
      label: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 16, color: Colors.white),
          SizedBox(width: 4),
          Text(text, style: TextStyle(color: Colors.white, fontSize: 12)),
        ],
      ),
      backgroundColor: color,
    );
  }

  Widget _buildTabs() {
    return Container(
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(color: Colors.grey.shade300),
        ),
      ),
      child: Row(
        children: [
          _tabItem('Cihaz Ekle', Icons.add_circle, 0),
          _tabItem('Cihaz Seç', Icons.devices, 1),
          _tabItem('Raporlar', Icons.description, 2),
          _tabItem('İstatistikler', Icons.bar_chart, 3),
        ],
      ),
    );
  }

  Widget _tabItem(String title, IconData icon, int index) {
    bool isSelected = _selectedTab == index;
    return Expanded(
      child: InkWell(
        onTap: () => setState(() => _selectedTab = index),
        child: Container(
          padding: EdgeInsets.symmetric(vertical: 16),
          decoration: BoxDecoration(
            border: Border(
              bottom: BorderSide(
                width: 3,
                color: isSelected ? Colors.blue.shade700 : Colors.transparent,
              ),
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, color: isSelected ? Colors.blue.shade700 : Colors.grey),
              SizedBox(width: 8),
              Text(
                title,
                style: TextStyle(
                  color: isSelected ? Colors.blue.shade700 : Colors.grey,
                  fontWeight: isSelected ? FontWeight.bold : FontWeight.normal,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildTabContent() {
    switch (_selectedTab) {
      case 0:
        return _CihazEklePage();
      case 1:
        return _CihazSecPage();
      case 2:
        return _RaporlarPage();
      case 3:
        return _IstatistiklerPage();
      default:
        return Container();
    }
  }
}

// Cihaz Ekle Tab
class _CihazEklePage extends StatefulWidget {
  @override
  _CihazEklePageState createState() => _CihazEklePageState();
}

class _CihazEklePageState extends State<_CihazEklePage> {
  final _formKey = GlobalKey<FormState>();
  final _cihazAdiController = TextEditingController();
  final _cihazKoduController = TextEditingController();
  final _markaController = TextEditingController();
  final _modelController = TextEditingController();
  String? _secilenTip;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.all(16),
      child: Card(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Form(
            key: _formKey,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Yeni Cihaz Ekle',
                  style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
                SizedBox(height: 24),
                TextFormField(
                  controller: _cihazAdiController,
                  decoration: InputDecoration(
                    labelText: 'Cihaz Adı',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.devices),
                  ),
                  validator: (value) {
                    if (value?.isEmpty ?? true) return 'Bu alan zorunludur';
                    return null;
                  },
                ),
                SizedBox(height: 16),
                TextFormField(
                  controller: _cihazKoduController,
                  decoration: InputDecoration(
                    labelText: 'Cihaz Kodu (ör: DK-001)',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.qr_code),
                  ),
                  validator: (value) {
                    if (value?.isEmpty ?? true) return 'Bu alan zorunludur';
                    return null;
                  },
                ),
                SizedBox(height: 16),
                DropdownButtonFormField<String>(
                  value: _secilenTip,
                  decoration: InputDecoration(
                    labelText: 'Cihaz Tipi',
                    border: OutlineInputBorder(),
                    prefixIcon: Icon(Icons.category),
                  ),
                  items: [
                    DropdownMenuItem(value: 'kumpas', child: Text('Kumpas')),
                    DropdownMenuItem(value: 'mikrometre', child: Text('Mikrometre')),
                    DropdownMenuItem(value: 'terazi', child: Text('Terazi')),
                    DropdownMenuItem(value: 'basinc_transmitteri', child: Text('Basınç Transmitteri')),
                    DropdownMenuItem(value: 'sicaklik_olcer', child: Text('Sıcaklık Ölçer')),
                    DropdownMenuItem(value: 'multimetre', child: Text('Multimetre')),
                  ],
                  onChanged: (value) {
                    setState(() => _secilenTip = value);
                  },
                  validator: (value) {
                    if (value == null) return 'Bu alan zorunludur';
                    return null;
                  },
                ),
                SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: TextFormField(
                        controller: _markaController,
                        decoration: InputDecoration(
                          labelText: 'Marka',
                          border: OutlineInputBorder(),
                        ),
                      ),
                    ),
                    SizedBox(width: 16),
                    Expanded(
                      child: TextFormField(
                        controller: _modelController,
                        decoration: InputDecoration(
                          labelText: 'Model',
                          border: OutlineInputBorder(),
                        ),
                      ),
                    ),
                  ],
                ),
                Spacer(),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: _cihazKaydet,
                    child: Text('Cihazı Kaydet'),
                    style: ElevatedButton.styleFrom(
                      padding: EdgeInsets.symmetric(vertical: 16),
                      backgroundColor: Colors.blue.shade700,
                      foregroundColor: Colors.white,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  void _cihazKaydet() async {
    if (_formKey.currentState!.validate()) {
      try {
        final response = await http.post(
          Uri.parse('http://localhost:8000/api/cihazlar'),
          headers: {'Content-Type': 'application/json'},
          body: json.encode({
            'cihaz_kodu': _cihazKoduController.text,
            'cihaz_adi': _cihazAdiController.text,
            'cihaz_tipi': _secilenTip!,
            'marka': _markaController.text,
            'model': _modelController.text,
            'seri_no': DateTime.now().millisecondsSinceEpoch.toString(),
            'olcme_araligi': '0-150 mm',
            'cozunurluk': '0.01 mm',
          }),
        );
        
        if (response.statusCode == 200) {
          final result = json.decode(response.body);
          
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Cihaz başarıyla kaydedildi! (ID: ${result['id']})'),
              backgroundColor: Colors.green,
            ),
          );
          
          _cihazAdiController.clear();
          _cihazKoduController.clear();
          _markaController.clear();
          _modelController.clear();
          setState(() => _secilenTip = null);
          
          if (mounted) {
            final parent = context.findAncestorStateOfType<_OrganizasyonDetayPageState>();
            parent?.setState(() => parent._selectedTab = 1);
          }
        } else {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Hata: ${response.statusCode}'),
              backgroundColor: Colors.red,
            ),
          );
        }
      } catch (e) {
        print('Cihaz kaydetme hatası: $e');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Bağlantı hatası: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  @override
  void dispose() {
    _cihazAdiController.dispose();
    _cihazKoduController.dispose();
    _markaController.dispose();
    _modelController.dispose();
    super.dispose();
  }
}

// Cihaz Seç Tab
class _CihazSecPage extends StatefulWidget {
  @override
  _CihazSecPageState createState() => _CihazSecPageState();
}

class _CihazSecPageState extends State<_CihazSecPage> {
  List<Map<String, dynamic>> cihazlar = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadCihazlar();
  }

  Future<void> _loadCihazlar() async {
    try {
      final response = await http.get(
        Uri.parse('http://localhost:8000/api/cihazlar'),
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          cihazlar = List<Map<String, dynamic>>.from(data['cihazlar']);
          _isLoading = false;
        });
      }
    } catch (e) {
      print('Cihaz yükleme hatası: $e');
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return Center(child: CircularProgressIndicator());
    }
    
    if (cihazlar.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.devices, size: 64, color: Colors.grey),
            SizedBox(height: 16),
            Text('Henüz cihaz eklenmemiş'),
            SizedBox(height: 16),
            ElevatedButton(
              onPressed: () {
                final parent = context.findAncestorStateOfType<_OrganizasyonDetayPageState>();
                parent?.setState(() => parent._selectedTab = 0);
              },
              child: Text('Cihaz Ekle'),
            ),
          ],
        ),
      );
    }
    
    return Padding(
      padding: EdgeInsets.all(16),
      child: ListView.builder(
        itemCount: cihazlar.length,
        itemBuilder: (context, index) {
          final cihaz = cihazlar[index];
          return Card(
            margin: EdgeInsets.only(bottom: 12),
            child: ListTile(
              leading: CircleAvatar(
                backgroundColor: _getDurumColor(cihaz['durum']),
                child: Icon(Icons.build, color: Colors.white),
              ),
              title: Text(
                '${cihaz['kod']} - ${cihaz['ad']}',
                style: TextStyle(fontWeight: FontWeight.bold),
              ),
              subtitle: Text('${cihaz['marka']} ${cihaz['model']}'),
              trailing: ElevatedButton(
                onPressed: () {
                  Navigator.pushNamed(
                    context,
                    '/kalibrasyon-form',
                    arguments: cihaz,
                  );
                },
                child: Text('Kalibrasyon Başlat'),
              ),
            ),
          );
        },
      ),
    );
  }

  Color _getDurumColor(String durum) {
    switch (durum) {
      case 'tamamlandi':
        return Colors.green;
      case 'devam_ediyor':
        return Colors.orange;
      default:
        return Colors.grey;
    }
  }
}

// Raporlar Tab
class _RaporlarPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text('Raporlar sayfası - Yakında'),
    );
  }
}

// İstatistikler Tab
class _IstatistiklerPage extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Center(
      child: Text('İstatistikler sayfası - Yakında'),
    );
  }
}
