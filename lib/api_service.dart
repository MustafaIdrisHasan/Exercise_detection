import 'package:http/http.dart' as http;
import 'dart:convert';

class ApiService {
  final String baseUrl = 'http://127.0.0.1:5000';

  /// Start an exercise detection by sending POST request to the backend
  Future<Map<String, dynamic>> startExercise(String endpoint) async {
    final response = await http.post(
      Uri.parse('$baseUrl/$endpoint'),
      headers: <String, String>{
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: jsonEncode({}),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to start exercise: ${response.statusCode}');
    }
  }

  /// Generic POST method for sending data
  Future<Map<String, dynamic>> postData(String endpoint, Map<String, dynamic> data) async {
    final response = await http.post(
      Uri.parse('$baseUrl/$endpoint'),
      headers: <String, String>{
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: jsonEncode(data),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to post data: ${response.statusCode}');
    }
  }

  /// Get current exercise status
  Future<Map<String, dynamic>> getStatus() async {
    final response = await http.get(
      Uri.parse('$baseUrl/status'),
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to get status: ${response.statusCode}');
    }
  }

  /// Stop current exercise
  Future<Map<String, dynamic>> stopExercise() async {
    final response = await http.post(
      Uri.parse('$baseUrl/stop'),
      headers: <String, String>{
        'Content-Type': 'application/json; charset=UTF-8',
      },
    );
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    } else {
      throw Exception('Failed to stop exercise: ${response.statusCode}');
    }
  }

  /// Health check endpoint
  Future<bool> healthCheck() async {
    try {
      final response = await http.get(
        Uri.parse('$baseUrl/health'),
      );
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }
}
