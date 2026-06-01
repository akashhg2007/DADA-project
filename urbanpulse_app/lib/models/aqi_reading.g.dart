// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'aqi_reading.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AqiReading _$AqiReadingFromJson(Map<String, dynamic> json) => AqiReading(
  location: json['location'] as String,
  timestamp: DateTime.parse(json['timestamp'] as String),
  aqi: (json['AQI'] as num).toDouble(),
  pm25: (json['PM2.5'] as num?)?.toDouble(),
  pm10: (json['PM10'] as num?)?.toDouble(),
  no2: (json['NO2'] as num?)?.toDouble(),
  so2: (json['SO2'] as num?)?.toDouble(),
);

Map<String, dynamic> _$AqiReadingToJson(AqiReading instance) =>
    <String, dynamic>{
      'location': instance.location,
      'timestamp': instance.timestamp.toIso8601String(),
      'AQI': instance.aqi,
      'PM2.5': instance.pm25,
      'PM10': instance.pm10,
      'NO2': instance.no2,
      'SO2': instance.so2,
    };
