// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'aqi_model.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

AqiModel _$AqiModelFromJson(Map<String, dynamic> json) => AqiModel(
  timestamp: json['timestamp'] as String,
  ward: json['ward'] as String,
  aqi: (json['aqi'] as num).toDouble(),
  pm25: (json['pm25'] as num).toDouble(),
  congestion: (json['congestion'] as num).toDouble(),
);

Map<String, dynamic> _$AqiModelToJson(AqiModel instance) => <String, dynamic>{
  'timestamp': instance.timestamp,
  'ward': instance.ward,
  'aqi': instance.aqi,
  'pm25': instance.pm25,
  'congestion': instance.congestion,
};
