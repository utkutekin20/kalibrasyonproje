import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'package:intl/intl.dart';

class RaporlarPage extends StatefulWidget {
  @override
  _RaporlarPageState createState() => _RaporlarPageState();
}

class _RaporlarPageState extends State<RaporlarPage> {
  List<Map<String, dynamic>> _raporlar = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadRaporlar();
  }

  Future<void> _loadRaporlar() async {
    try {
      final response = await http.get(
        Uri.parse('http://localhost:8000/api/reports'),
      );
      
      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        setState(() {
          _raporlar = List<Map<String, dynamic>>.from(data['reports']);
          _isLoading = false;
        });
      }
    } catch (e) {
      print('Rapor yükleme hatası: $e');
      setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Kalibrasyon Raporları'),
        backgroundColor: Colors.blue.shade700,
        actions: [
          IconButton(
            icon: Icon(Icons.refresh),
            onPressed: _loadRaporlar,
          ),
        ],
      ),
      body: _isLoading
          ? Center(child: CircularProgressIndicator())
          : _raporlar.isEmpty
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.description, size: 64, color: Colors.grey),
                      SizedBox(height: 16),
                      Text('Henüz rapor bulunmuyor'),
                    ],
                  ),
                )
              : ListView.builder(
                  padding: EdgeInsets.all(16),
                  itemCount: _raporlar.length,
                  itemBuilder: (context, index) {
                    final rapor = _raporlar[index];
                    return Card(
                      margin: EdgeInsets.only(bottom: 12),
                      child: ListTile(
                        leading: CircleAvatar(
                          backgroundColor: rapor['uygunluk'] ? Colors.green : Colors.red,
                          child: Icon(
                            rapor['uygunluk'] ? Icons.check : Icons.close,
                            color: Colors.white,
                          ),
                        ),
                        title: Text(
                          rapor['sertifika_no'] ?? 'Sertifika No Yok',
                          style: TextStyle(fontWeight: FontWeight.bold),
                        ),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text('Cihaz: ${rapor['cihaz_tipi'] ?? ''} - ${rapor['seri_no'] ?? ''}'),
                            Text('Müşteri: ${rapor['musteri_adi'] ?? ''}'),
                            Text(
                              'Tarih: ${_formatTarih(rapor['kalibrasyon_tarihi'])}',
                              style: TextStyle(fontSize: 12),
                            ),
                          ],
                        ),
                        trailing: PopupMenuButton<String>(
                          onSelected: (value) {
                            if (value == 'pdf') {
                              _downloadPdf(rapor['id']);
                            } else if (value == 'delete') {
                              _deleteRapor(rapor['id']);
                            }
                          },
                          itemBuilder: (context) => [
                            PopupMenuItem(
                              value: 'pdf',
                              child: Row(
                                children: [
                                  Icon(Icons.picture_as_pdf, color: Colors.red, size: 20),
                                  SizedBox(width: 8),
                                  Text('PDF İndir'),
                                ],
                              ),
                            ),
                            PopupMenuItem(
                              value: 'delete',
                              child: Row(
                                children: [
                                  Icon(Icons.delete, color: Colors.grey, size: 20),
                                  SizedBox(width: 8),
                                  Text('Sil'),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  },
                ),
    );
  }

  String _formatTarih(String? tarih) {
    if (tarih == null) return '-';
    
    try {
      // ISO formatını kontrol et
      final date = DateTime.parse(tarih);
      return DateFormat('dd.MM.yyyy').format(date);
    } catch (e) {
      // Alternatif formatları dene
      try {
        final parts = tarih.split('-');
        if (parts.length >= 3) {
          return '${parts[2].substring(0, 2)}.${parts[1]}.${parts[0]}';
        }
      } catch (e2) {}
      
      return tarih; // Ham veriyi göster
    }
  }

  void _downloadPdf(int id) {
    // PDF indirme işlemi
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text('PDF indiriliyor...')),
    );
  }

  void _deleteRapor(int id) async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Raporu Sil'),
        content: Text('Bu raporu silmek istediğinizden emin misiniz?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('İptal'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text('Sil', style: TextStyle(color: Colors.red)),
          ),
        ],
      ),
    );

    if (confirm == true) {
      try {
        final response = await http.delete(
          Uri.parse('http://localhost:8000/api/reports/$id'),
        );
        
        if (response.statusCode == 200) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Rapor silindi')),
          );
          _loadRaporlar();
        }
      } catch (e) {
        print('Silme hatası: $e');
      }
    }
  }
}
