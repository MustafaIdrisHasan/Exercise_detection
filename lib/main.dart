import 'package:flutter/material.dart';
import 'api_service.dart';
import 'package:logging/logging.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return const MaterialApp(
      home: HomeScreen(),
    );
  }
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({Key? key}) : super(key: key);

  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final ApiService apiService = ApiService();
  String message = '';

  final Logger _logger = Logger('HomeScreen');

  void startExercise(String endpoint) async {
    try {
      final response = await apiService.startExercise(endpoint);
      setState(() {
        message = response['status'] ?? 'Exercise started';
      });
      _logger.info(response.toString());
    } catch (e) {
      setState(() {
        message = 'Error: ${e.toString()}';
      });
      _logger.severe(e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Exercise Detection'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: <Widget>[
            ElevatedButton(
              onPressed: () => startExercise('lateral_raises'),
              child: const Text('Start Lateral Raises Detection'),
            ),
            ElevatedButton(
              onPressed: () => startExercise('shoulder_press'),
              child: const Text('Start Shoulder Press Detection'),
            ),
            ElevatedButton(
              onPressed: () => startExercise('crunches'),
              child: const Text('Start Crunches Detection'),
            ),
            ElevatedButton(
              onPressed: () => startExercise('bicep_curls'),
              child: const Text('Start Bicep Curls Detection'),
            ),
            const SizedBox(height: 20),
            Text(message),
          ],
        ),
      ),
    );
  }
}
