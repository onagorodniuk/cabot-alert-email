from os import environ as env

from django.conf import settings
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.template import Context, Template

from cabot.cabotapp.alert import AlertPlugin

import requests
import logging

"""Service {{ service.name }} {{ scheme }}://{{ host }}{% url 'service' pk=service.id %} {% if service.overall_status != service.PASSING_STATUS %}alerting with status: {{ service.overall_status }}{% else %}is back to normal{% endif %}.
{% if service.overall_status != service.PASSING_STATUS %}
CHECKS FAILING:{% for check in service.all_failing_checks %}
  FAILING:  {% if check.check_category == 'Jenkins check' %}{% if check.last_result.error %} {{ check.name }} ({{ check.last_result.error|safe }}) {{jenkins_api}}job/{{ check.name }}/{{ check.last_result.job_number }}/console{% else %} {{ check.name }} {{jenkins_api}}/job/{{ check.name }}/{{check.last_result.job_number}}/console {% endif %}{% else %}
    {{ check.name }}:
      {{check.metric|truncatechars:70}}:
       {% if check.last_result.error %} {{ check.last_result.error|safe }}{% endif %}{% endif %}{% endfor %}
{% if service.all_passing_checks %}
Passing checks:{% for check in service.all_passing_checks %}
  PASSING - {{ check.name }} - {{check.metric|truncatechars:70}} {% endfor %}
{% endif %}
{% endif %}
"""

class EmailAlert(AlertPlugin):
    name = "Email"
    author = "Oleksandr Nagorodniuk"

    def send_alert(self, service, users, duty_officers):
        emails = [u.email for u in users if u.email]
        if not emails:
            return
        c = Context({
            'service': service,
            'host': settings.WWW_HTTP_HOST,
            'scheme': settings.WWW_SCHEME
        })
        if service.overall_status != service.PASSING_STATUS:
            if service.overall_status == service.CRITICAL_STATUS:
                emails += [u.email for u in users if u.email]
            subject = '%s status for service: %s' % (
                service.overall_status, service.name)
        else:
            subject = 'Service back to normal: %s' % (service.name,)
        t = Template(email_template)
        send_mail(
            subject=subject,
            message=t.render(c),
            from_email='Cabot <%s>' % env.get('CABOT_FROM_EMAIL'),
            recipient_list=emails,
        )
