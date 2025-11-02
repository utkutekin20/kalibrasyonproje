import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class OrganizasyonListPage extends StatefulWidget {
  @override
  _OrganizasyonListPageState createState() => _OrganizasyonListPageState();
}

class _OrganizasyonListPageState extends State<OrganizasyonListPage> {
  List<Map<String, dynamic>> _organizasyonlar = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadOrganizasyonlar();
  }

  Future<void> _loadOrganizasyonlar() async {
    try {
      final response = await http.get(
        Uri.parse('http://localhost:8000/api/organizasyonlar'),
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _organizasyonlar = data['organizasyonlar'].map<Map<String, dynamic>>((org) => {
            'id': org['id'],
            'ad': org['ad'],
            'musteri': org['musteri'],
            'baslangic': org['baslangic'] != null ? DateTime.tryParse(org['baslangic']) ?? DateTime.now() : DateTime.now(),
            'durum': org['durum'],
            'cihaz_sayisi': org['cihaz_sayisi'] ?? 0,
            'tamamlanan': org['tamamlanan'] ?? 0,
          }).toList();
          _isLoading = false;
        });
      }
    } catch (e) {
      print('Organizasyon yükleme hatası: $e');
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Kalibrasyon Organizasyonları'),
        backgroundColor: Colors.blue.shade700,
        actions: [
          IconButton(
            icon: Icon(Icons.description),
            onPressed: () => Navigator.pushNamed(context, '/raporlar'),
            tooltip: 'Tüm Raporlar',
          ),
        ],
      ),
      body: _isLoading 
          ? Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: _loadOrganizasyonlar,
              child: Column(
                children: [
                  _buildStats(),
                  Expanded(
                    child: _buildOrganizasyonList(),
                  ),
                ],
              ),
            ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: _yeniOrganizasyon,
        icon: Icon(Icons.add),
        label: Text('Yeni Organizasyon'),
        backgroundColor: Colors.blue.shade700,
      ),
    );
  }

  Widget _buildStats() {
    int devamEden = _organizasyonlar.where((o) => o['durum'] == 'devam_ediyor').length;
    int tamamlanan = _organizasyonlar.where((o) => o['durum'] == 'tamamlandi').length;

    return Container(
      padding: EdgeInsets.all(16),
      color: Colors.grey.shade100,
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _StatCard(
            title: 'Devam Eden',
            value: devamEden.toString(),
            color: Colors.orange,
            icon: Icons.schedule,
          ),
          _StatCard(
            title: 'Tamamlanan',
            value: tamamlanan.toString(),
            color: Colors.green,
            icon: Icons.check_circle,
          ),
          _StatCard(
            title: 'Toplam',
            value: _organizasyonlar.length.toString(),
            color: Colors.blue,
            icon: Icons.assessment,
          ),
        ],
      ),
    );
  }

  Widget _buildOrganizasyonList() {
    return ListView.builder(
      padding: EdgeInsets.all(16),
      itemCount: _organizasyonlar.length,
      itemBuilder: (context, index) {
        final org = _organizasyonlar[index];
        return Card(
          margin: EdgeInsets.only(bottom: 16),
          child: InkWell(
            onTap: () => _organizasyonDetay(org),
            borderRadius: BorderRadius.circular(12),
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          org['ad'],
                          style: TextStyle(
                            fontSize: 18,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                      _durumChip(org['durum']),
                    ],
                  ),
                  SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(Icons.business, size: 16, color: Colors.grey),
                      SizedBox(width: 4),
                      Text(
                        org['musteri'],
                        style: TextStyle(color: Colors.grey.shade700),
                      ),
                    ],
                  ),
                  SizedBox(height: 4),
                  Row(
                    children: [
                      Icon(Icons.calendar_today, size: 16, color: Colors.grey),
                      SizedBox(width: 4),
                      Text(
                        'Başlangıç: ${DateFormat('dd.MM.yyyy').format(org['baslangic'])}',
                        style: TextStyle(color: Colors.grey.shade700),
                      ),
                    ],
                  ),
                  SizedBox(height: 12),
                  LinearProgressIndicator(
                    value: (org['cihaz_sayisi'] ?? 0) > 0 
                        ? (org['tamamlanan'] ?? 0) / org['cihaz_sayisi'] 
                        : 0,
                    backgroundColor: Colors.grey.shade300,
                    valueColor: AlwaysStoppedAnimation<Color>(
                      org['durum'] == 'tamamlandi' ? Colors.green : Colors.blue,
                    ),
                  ),
                  SizedBox(height: 4),
                  Text(
                    '${org['tamamlanan'] ?? 0} / ${org['cihaz_sayisi'] ?? 0} cihaz tamamlandı',
                    style: TextStyle(fontSize: 12, color: Colors.grey.shade600),
                  ),
                ],
              ),
            ),
          ),
        );
      },
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
        icon = Icons.schedule;
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
          Text(text, style: TextStyle(color: Colors.white)),
        ],
      ),
      backgroundColor: color,
    );
  }

  void _yeniOrganizasyon() {
    // Yeni organizasyon oluşturma sayfasına git
    Navigator.pushNamed(context, '/yeni-organizasyon');
  }

  void _organizasyonDetay(Map<String, dynamic> org) {
    // Organizasyon detay sayfasına git
    Navigator.pushNamed(context, '/organizasyon-detay', arguments: org);
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final String value;
  final Color color;
  final IconData icon;

  const _StatCard({
    required this.title,
    required this.value,
    required this.color,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: Colors.grey.shade200,
            blurRadius: 6,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        children: [
          Icon(icon, color: color, size: 32),
          SizedBox(height: 8),
          Text(
            value,
            style: TextStyle(
              fontSize: 24,
              fontWeight: FontWeight.bold,
              color: color,
            ),
          ),
          SizedBox(height: 4),
          Text(
            title,
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey.shade600,
            ),
          ),
        ],
      ),
    );
  }
}
