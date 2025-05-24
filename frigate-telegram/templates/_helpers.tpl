{{- define "frigate-telegram.name" -}}
{{ .Chart.Name }}
{{- end }}

{{- define "frigate-telegram.fullname" -}}
{{ .Release.Name }}
{{- end }}
