import 'package:flutter/material.dart';
import 'screens/home_page.dart';
import 'screens/organizasyon_list_page.dart';
import 'screens/organizasyon_detay_page.dart';
import 'screens/kalibrasyon_form_page.dart';
import 'screens/yeni_organizasyon_page.dart';
import 'screens/raporlar_page.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Kalibrasyon Yönetim Sistemi',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
        useMaterial3: true,
      ),
      home: OrganizasyonListPage(), // Yeni ana sayfa
      routes: {
        '/home': (context) => HomePage(),
        '/organizasyonlar': (context) => OrganizasyonListPage(),
        '/organizasyon-detay': (context) => OrganizasyonDetayPage(),
        '/kalibrasyon-form': (context) => KalibrasyonFormPage(),
        '/yeni-organizasyon': (context) => YeniOrganizasyonPage(),
        '/raporlar': (context) => RaporlarPage(),
      },
    );
  }
}
