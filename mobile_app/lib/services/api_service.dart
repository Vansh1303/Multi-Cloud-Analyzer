import 'dart:convert';
import 'package:http/http.dart' as http;

class ApiService {
  // Use 10.0.2.2 for Android Emulator, localhost for iOS simulator/desktop
  static const String baseUrl = 'http://13.206.95.24:8000';

  Future<Map<String, dynamic>> fetchTelemetry() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/telemetry'));
      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to load telemetry');
      }
    } catch (e) {
      throw Exception('Failed to connect to API: $e');
    }
  }

  Future<bool> runBenchmark(String token) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/run'),
        headers: {
          'Authorization': 'Bearer $token',
          'Content-Type': 'application/json',
        },
      );
      return response.statusCode == 200;
    } catch (e) {
      throw Exception('Failed to trigger benchmark: $e');
    }
  }
}
