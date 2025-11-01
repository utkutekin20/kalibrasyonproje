import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';
import 'report_page.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'dart:html' as html;
import 'dart:async';

class RecordPage extends StatefulWidget {
  const RecordPage({super.key});

  @override
  State<RecordPage> createState() => _RecordPageState();
}

class _RecordPageState extends State<RecordPage> {
  bool _isRecording = false;
  bool _isProcessing = false;
  bool _hasRecording = false;
  String _transcribedText = '';
  html.MediaRecorder? _mediaRecorder;
  List<html.Blob> _recordedChunks = [];
  html.Blob? _audioBlob;
  
  // Görsel analiz için yeni değişkenler
  html.Blob? _imageBlob;
  String? _imageBase64;
  Map<String, dynamic>? _imageAnalysis;
  bool _hasImage = false;

  @override
  void dispose() {
    super.dispose();
  }

  Future<void> _startRecording() async {
    try {
      final stream = await html.window.navigator.mediaDevices!.getUserMedia({'audio': true});
      
      _mediaRecorder = html.MediaRecorder(stream);
      _recordedChunks.clear();
      
      _mediaRecorder!.addEventListener('dataavailable', (event) {
        final blobEvent = event as html.BlobEvent;
        if (blobEvent.data != null && blobEvent.data!.size > 0) {
          _recordedChunks.add(blobEvent.data!);
        }
      });
      
      _mediaRecorder!.addEventListener('stop', (event) {
        _audioBlob = html.Blob(_recordedChunks, 'audio/webm');
      });
      
      _mediaRecorder!.start();
      
      setState(() {
        _isRecording = true;
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ses kaydı başladı - konuşmaya başlayabilirsiniz!')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Mikrofon erişimi reddedildi: $e')),
      );
    }
  }

  Future<void> _stopRecording() async {
    if (_mediaRecorder != null) {
      _mediaRecorder!.stop();
      _mediaRecorder!.stream!.getTracks().forEach((track) => track.stop());
      
      // Kaydın tamamlanması için kısa bir süre bekle
      await Future.delayed(const Duration(milliseconds: 500));
      
      setState(() {
        _isRecording = false;
        _hasRecording = true;
      });
      
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Ses kaydı tamamlandı! Şimdi rapor oluşturabilirsiniz.')),
      );
    }
  }

  // Fotoğraf yükleme ve analiz etme
  Future<void> _pickAndAnalyzeImage() async {
    try {
      setState(() {
        _isProcessing = true;
      });

      final html.FileUploadInputElement uploadInput = html.FileUploadInputElement();
      uploadInput.accept = 'image/*';
      uploadInput.click();

      await uploadInput.onChange.first;

      final html.File? file = uploadInput.files?.first;
      if (file == null) {
        setState(() {
          _isProcessing = false;
        });
        return;
      }

      // Dosyayı oku
      final reader = html.FileReader();
      reader.readAsArrayBuffer(file);
      await reader.onLoad.first;

      final data = reader.result as List<int>;
      _imageBlob = html.Blob([data], file.type);
      _imageBase64 = base64Encode(data);

      // Backend'e gönder
      final formData = html.FormData();
      formData.appendBlob('file', _imageBlob!, file.name);

      final xhr = html.HttpRequest();
      xhr.open('POST', 'http://localhost:8000/api/analyze-image');

      final completer = Completer<String>();

      xhr.onLoad.listen((event) {
        if (xhr.status == 200) {
          completer.complete(xhr.responseText!);
        } else {
          completer.completeError('Görsel analiz hatası: ${xhr.status}');
        }
      });

      xhr.onError.listen((event) {
        completer.completeError('Network hatası');
      });

      xhr.send(formData);

      final analysisText = await completer.future;
      final analysisData = json.decode(analysisText);

      setState(() {
        _imageAnalysis = analysisData['analysis'];
        _hasImage = true;
        _isProcessing = false;
      });

      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Görsel analizi tamamlandı!')),
      );
    } catch (e) {
      setState(() {
        _isProcessing = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Görsel analiz hatası: $e')),
      );
    }
  }

  Future<void> _createReport() async {
    if (!_hasRecording || _audioBlob == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Önce ses kaydı yapmalısınız!')),
      );
      return;
    }

    setState(() {
      _isProcessing = true;
    });

    try {
      // 1. Ses dosyasını metne çevir (Whisper)
      final formData = html.FormData();
      formData.appendBlob('file', _audioBlob!, 'recording.webm');
      
      final xhr = html.HttpRequest();
      xhr.open('POST', 'http://localhost:8000/api/speech-to-text');
      
      final completer = Completer<String>();
      
      xhr.onLoad.listen((event) {
        if (xhr.status == 200) {
          completer.complete(xhr.responseText!);
        } else {
          completer.completeError('Transkripsiyon hatası: ${xhr.status}');
        }
      });
      
      xhr.onError.listen((event) {
        completer.completeError('Network hatası');
      });
      
      xhr.send(formData);
      
      final transcriptionText = await completer.future;
      final transcriptionData = json.decode(transcriptionText);
      _transcribedText = transcriptionData['text'] ?? '';
      
      if (_transcribedText.isEmpty) {
        throw Exception('Ses kaydından metin çıkarılamadı');
      }
      
      // 2. Rapor oluştur (GPT-4o-mini ile)
      final reportResponse = await http.post(
        Uri.parse('http://localhost:8000/api/generate-report'),
        headers: {'Content-Type': 'application/json'},
        body: json.encode({'text': _transcribedText}),
      );
      
      if (reportResponse.statusCode != 200) {
        throw Exception('Rapor oluşturulamadı: ${reportResponse.statusCode}');
      }
      
      final reportData = json.decode(reportResponse.body);
      
      // Görsel analiz varsa ekle
      if (_hasImage && _imageAnalysis != null) {
        reportData['gorsel_analiz'] = {
          'image_base64': _imageBase64,
          ..._imageAnalysis!,
        };
      }

             // 3. PDF oluştur - Kalibrasyon sertifikası formatında
             final pdfResponse = await http.post(
               Uri.parse('http://localhost:8000/api/create-kalibrasyon-pdf'),
               headers: {'Content-Type': 'application/json'},
               body: json.encode(reportData),
             );

      if (pdfResponse.statusCode != 200) {
        throw Exception('PDF oluşturulamadı: ${pdfResponse.statusCode}');
      }

      // PDF'i base64 olarak kaydet (web için)
      final pdfBytes = pdfResponse.bodyBytes;
      final pdfBase64 = base64Encode(pdfBytes);

      setState(() {
        _isProcessing = false;
      });

      // Rapor sayfasına git
      Navigator.pushReplacement(
        context,
        MaterialPageRoute(
          builder: (context) => ReportPage(
            pdfPath: pdfBase64,
            transcribedText: _transcribedText,
            reportData: reportData,
          ),
        ),
      );
    } catch (e) {
      setState(() {
        _isProcessing = false;
      });
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Hata: $e')),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF5F7FA),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1E3A8A),
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back, color: Colors.white),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Yeni Rapor Olustur',
              style: TextStyle(
                color: Colors.white,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),
            Text(
              'Adim 1: Ses Kaydi ve Gorsel',
              style: TextStyle(
                color: Colors.white70,
                fontSize: 12,
              ),
            ),
          ],
        ),
      ),
      body: _isProcessing
          ? Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: Colors.black.withOpacity(0.1),
                          blurRadius: 20,
                          offset: const Offset(0, 10),
                        ),
                      ],
                    ),
                    child: const CircularProgressIndicator(
                      strokeWidth: 3,
                      valueColor: AlwaysStoppedAnimation<Color>(Color(0xFF1E3A8A)),
                    ),
                  ),
                  const SizedBox(height: 24),
                  const Text(
                    'Islem yapiliyor...',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w500,
                      color: Color(0xFF1E293B),
                    ),
                  ),
                  const SizedBox(height: 8),
                  const Text(
                    'Lutfen bekleyin',
                    style: TextStyle(
                      fontSize: 14,
                      color: Color(0xFF64748B),
                    ),
                  ),
                ],
              ),
            )
          : SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  // Ses Kayıt Kartı
                  _buildCard(
                    title: '1. Ses Kaydi',
                    subtitle: _isRecording
                        ? 'Kayit devam ediyor...'
                        : _hasRecording
                            ? 'Kayit tamamlandi'
                            : 'Cihaz bilgilerini anlatın',
                    icon: Icons.mic,
                    iconColor: _isRecording
                        ? Colors.red
                        : _hasRecording
                            ? const Color(0xFF10B981)
                            : const Color(0xFF3B82F6),
                    child: Column(
                      children: [
                        if (_isRecording)
                          Column(
                            children: [
                              Container(
                                padding: const EdgeInsets.all(20),
                                decoration: BoxDecoration(
                                  color: Colors.red.withOpacity(0.1),
                                  shape: BoxShape.circle,
                                ),
                                child: const Icon(
                                  Icons.fiber_manual_record,
                                  color: Colors.red,
                                  size: 80,
                                ),
                              ),
                              const SizedBox(height: 16),
                              const Text(
                                'Kayit Yapiliyor...',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                  color: Colors.red,
                                ),
                              ),
                            ],
                          ),
                        if (!_isRecording && !_hasRecording)
                          const Icon(
                            Icons.mic_none,
                            size: 80,
                            color: Color(0xFF3B82F6),
                          ),
                        if (_hasRecording && !_isRecording)
                          const Icon(
                            Icons.check_circle,
                            size: 80,
                            color: Color(0xFF10B981),
                          ),
                        const SizedBox(height: 20),
                        SizedBox(
                          width: double.infinity,
                          child: ElevatedButton.icon(
                            onPressed: _isRecording ? _stopRecording : _startRecording,
                            icon: Icon(_isRecording ? Icons.stop : Icons.mic, size: 24),
                            label: Text(
                              _isRecording ? 'Kaydi Durdur' : 'Kayda Basla',
                              style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                              ),
                            ),
                            style: ElevatedButton.styleFrom(
                              backgroundColor: _isRecording ? Colors.red : const Color(0xFF3B82F6),
                              foregroundColor: Colors.white,
                              padding: const EdgeInsets.symmetric(vertical: 16),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                              elevation: 0,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  if (_hasRecording) ...[
                    const SizedBox(height: 20),
                    
                    // Görsel Analiz Kartı
                    _buildCard(
                      title: '2. Cihaz Fotografi (Opsiyonel)',
                      subtitle: _hasImage
                          ? 'Gorsel analizi tamamlandi'
                          : 'AI ile otomatik analiz',
                      icon: Icons.camera_alt,
                      iconColor: _hasImage ? const Color(0xFF10B981) : const Color(0xFFF59E0B),
                      child: Column(
                        children: [
                          if (!_hasImage)
                            const Icon(
                              Icons.add_a_photo,
                              size: 60,
                              color: Color(0xFFF59E0B),
                            ),
                          if (_hasImage && _imageAnalysis != null)
                            Container(
                              padding: const EdgeInsets.all(16),
                              decoration: BoxDecoration(
                                color: const Color(0xFF10B981).withOpacity(0.1),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Row(
                                    children: [
                                      Icon(Icons.check_circle, color: Color(0xFF10B981)),
                                      SizedBox(width: 8),
                                      Text(
                                        'Analiz Tamamlandi',
                                        style: TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 16,
                                        ),
                                      ),
                                    ],
                                  ),
                                  const SizedBox(height: 12),
                                  _buildAnalysisRow(
                                    'Cihaz',
                                    _imageAnalysis!['cihaz_turu'] ?? 'Belirtilmemis',
                                  ),
                                  _buildAnalysisRow(
                                    'Durum',
                                    _imageAnalysis!['gorsel_durum'] ?? 'Belirtilmemis',
                                  ),
                                ],
                              ),
                            ),
                          const SizedBox(height: 16),
                          SizedBox(
                            width: double.infinity,
                            child: ElevatedButton.icon(
                              onPressed: _pickAndAnalyzeImage,
                              icon: const Icon(Icons.add_photo_alternate, size: 24),
                              label: Text(
                                _hasImage ? 'Baska Fotograf Ekle' : 'Fotograf Yukle',
                                style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: _hasImage
                                    ? const Color(0xFF10B981)
                                    : const Color(0xFFF59E0B),
                                foregroundColor: Colors.white,
                                padding: const EdgeInsets.symmetric(vertical: 16),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                elevation: 0,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    
                    const SizedBox(height: 32),
                    
                    // Rapor Oluştur Butonu
                    Container(
                      padding: const EdgeInsets.all(20),
                      decoration: BoxDecoration(
                        gradient: const LinearGradient(
                          colors: [Color(0xFF1E3A8A), Color(0xFF3B82F6)],
                          begin: Alignment.topLeft,
                          end: Alignment.bottomRight,
                        ),
                        borderRadius: BorderRadius.circular(16),
                        boxShadow: [
                          BoxShadow(
                            color: const Color(0xFF1E3A8A).withOpacity(0.3),
                            blurRadius: 20,
                            offset: const Offset(0, 10),
                          ),
                        ],
                      ),
                      child: Column(
                        children: [
                          const Text(
                            'Rapor Olusturmaya Hazir!',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Text(
                            _hasImage
                                ? 'Ses kaydi ve gorsel analizi ile'
                                : 'Ses kaydi ile',
                            style: const TextStyle(
                              color: Colors.white70,
                              fontSize: 14,
                            ),
                          ),
                          const SizedBox(height: 16),
                          SizedBox(
                            width: double.infinity,
                            child: ElevatedButton.icon(
                              onPressed: _createReport,
                              icon: const Icon(Icons.rocket_launch, size: 28),
                              label: const Text(
                                'Rapor Olustur',
                                style: TextStyle(
                                  fontSize: 18,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                              style: ElevatedButton.styleFrom(
                                backgroundColor: Colors.white,
                                foregroundColor: const Color(0xFF1E3A8A),
                                padding: const EdgeInsets.symmetric(vertical: 18),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(12),
                                ),
                                elevation: 0,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
    );
  }

  Widget _buildCard({
    required String title,
    required String subtitle,
    required IconData icon,
    required Color iconColor,
    required Widget child,
  }) {
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: iconColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: iconColor, size: 24),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: Color(0xFF1E293B),
                      ),
                    ),
                    Text(
                      subtitle,
                      style: const TextStyle(
                        fontSize: 14,
                        color: Color(0xFF64748B),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 20),
          child,
        ],
      ),
    );
  }

  Widget _buildAnalysisRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        children: [
          Text(
            '$label: ',
            style: const TextStyle(
              fontWeight: FontWeight.w500,
              color: Color(0xFF64748B),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                color: Color(0xFF1E293B),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
