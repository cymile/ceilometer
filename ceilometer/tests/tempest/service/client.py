# Copyright 2014 OpenStack Foundation
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from oslo_serialization import jsonutils as json
from six.moves.urllib import parse as urllib

from tempest import clients
from tempest import config
from tempest.lib.common import rest_client


CONF = config.CONF


class TelemetryClient(rest_client.RestClient):

    version = '2'
    uri_prefix = "v2"

    def deserialize(self, body):
        return json.loads(body.replace("\n", ""))

    def serialize(self, body):
        return json.dumps(body)

    def create_sample(self, meter_name, sample_list):
        uri = "%s/meters/%s" % (self.uri_prefix, meter_name)
        body = self.serialize(sample_list)
        resp, body = self.post(uri, body)
        self.expected_success(200, resp.status)
        body = self.deserialize(body)
        return rest_client.ResponseBody(resp, body)

    def _helper_list(self, uri, query=None, period=None):
        uri_dict = {}
        if query:
            uri_dict = {'q.field': query[0],
                        'q.op': query[1],
                        'q.value': query[2]}
        if period:
            uri_dict['period'] = period
        if uri_dict:
            uri += "?%s" % urllib.urlencode(uri_dict)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        body = self.deserialize(body)
        return rest_client.ResponseBodyList(resp, body)

    def list_resources(self, query=None):
        uri = '%s/resources' % self.uri_prefix
        return self._helper_list(uri, query)

    def list_meters(self, query=None):
        uri = '%s/meters' % self.uri_prefix
        return self._helper_list(uri, query)

    def list_statistics(self, meter, period=None, query=None):
        uri = "%s/meters/%s/statistics" % (self.uri_prefix, meter)
        return self._helper_list(uri, query, period)

    def list_samples(self, meter_id, query=None):
        uri = '%s/meters/%s' % (self.uri_prefix, meter_id)
        return self._helper_list(uri, query)

    def show_resource(self, resource_id):
        uri = '%s/resources/%s' % (self.uri_prefix, resource_id)
        resp, body = self.get(uri)
        self.expected_success(200, resp.status)
        body = self.deserialize(body)
        return rest_client.ResponseBody(resp, body)


class Manager(clients.Manager):

    default_params = config.service_client_config()

    telemetry_params = {
        'service': CONF.telemetry.catalog_type,
        'region': CONF.identity.region,
        'endpoint_type': CONF.telemetry.endpoint_type,
    }
    telemetry_params.update(default_params)

    def __init__(self, credentials):
        # TODO(andreaf) Overriding Manager is a workaround. The "proper" way
        # would it to expose the ceilometer service client via the plugin
        # interface, use tempest.lib.clients and tempest master.
        # Then ceilometer service client would be loaded and configured
        # automatically into ServiceClients.
        # In any case we're about to declare clients.Manager a stable
        # interface for plugins and we won't change it, so this code won't
        # break.
        super(Manager, self).__init__(credentials=credentials)
        self.set_telemetry_client()

    def set_telemetry_client(self):
        self.telemetry_client = TelemetryClient(self.auth_provider,
                                                **self.telemetry_params)
