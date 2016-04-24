#!/usr/bin/env python
# -*- coding: utf-8 -*-

###############################################################################
# The MIT License
#
# Copyright (c) 2016 Grigory Chernyshev
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#
###############################################################################

import json

from yagocd.client import Yagocd
from yagocd.session import Session
from yagocd.resources import agent

import mock
import pytest


class BaseTestAgentManager(object):
    @pytest.fixture()
    def session(self):
        return Session(auth=None, options=Yagocd.DEFAULT_OPTIONS)

    @pytest.fixture()
    def manager(self, session):
        return agent.AgentManager(session=session)


class TestList(BaseTestAgentManager):
    def test_list_request_url(self, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_list") as cass:
            manager.list()
            assert cass.requests[0].path == '/go/api/agents'

    def test_list_request_method(self, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_list") as cass:
            manager.list()
            assert cass.requests[0].method == 'GET'

    def test_list_request_accept_headers(self, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_list") as cass:
            manager.list()
            assert cass.requests[0].headers['accept'] == 'application/vnd.go.cd.v2+json'

    def test_list_response_code(self, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_list") as cass:
            manager.list()
            assert cass.responses[0]['status']['code'] == 200

    def test_list_return_type(self, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_list"):
            result = manager.list()
            assert isinstance(result, list)

    def test_list_is_not_empty(self, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_list"):
            result = manager.list()
            assert len(result) > 0

    def test_list_returns_agent_entities(self, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_list"):
            result = manager.list()
            assert all(isinstance(i, agent.AgentEntity) for i in result)


class TestDict(BaseTestAgentManager):
    @mock.patch('yagocd.resources.agent.AgentManager.list')
    def test_dict_calls_list(self, mock_list, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_list"):
            manager.dict()
            mock_list.assert_called()

    def test_dict_return_type(self, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_list"):
            result = manager.dict()
            assert isinstance(result, dict)

    def test_dict_returns_str_as_keys(self, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_list"):
            result = manager.dict()
            assert all(isinstance(i, basestring) for i in result.keys())

    def test_dict_returns_agent_entities_as_values(self, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_list"):
            result = manager.dict()
            assert all(isinstance(i, agent.AgentEntity) for i in result.values())

    def test_dict_get_by_key(self, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_list"):
            uuid = '68e5d48c-753a-4395-a79c-1cb22d77a12f'
            result = manager.dict().get(uuid)
            fixture = json.load(open('tests/fixtures/resources/agent/{uuid}-from-list.json'.format(uuid=uuid)))
            assert dict(result.data) == fixture


class TestGet(BaseTestAgentManager):
    UUID = '68e5d48c-753a-4395-a79c-1cb22d77a12f'

    def test_get_request_url(self, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_get") as cass:
            manager.get(self.UUID)
            assert cass.requests[0].path == '/go/api/agents/{uuid}'.format(uuid=self.UUID)

    def test_get_request_method(self, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_get") as cass:
            manager.get(self.UUID)
            assert cass.requests[0].method == 'GET'

    def test_get_request_accept_headers(self, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_get") as cass:
            manager.get(self.UUID)
            assert cass.requests[0].headers['accept'] == 'application/vnd.go.cd.v1+json'

    def test_get_response_code(self, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_get") as cass:
            manager.get(self.UUID)
            assert cass.responses[0]['status']['code'] == 200

    def test_get_returns_instance_of_agent_entity(self, manager, my_vcr):
        with my_vcr.use_cassette("agent/agent_get"):
            result = manager.get(self.UUID)
            assert isinstance(result, agent.AgentEntity)