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

from yagocd.resources import BaseManager, Base
from yagocd.resources.stage import StageInstance

from easydict import EasyDict


class PipelineManager(BaseManager):
    """
    The pipelines API allows users to view pipeline information and operate on it.
    """

    @staticmethod
    def tie_descendants(pipelines):
        """
        Static method for tie-ing (linking) relevant pipelines.

        By default each pipeline object gives information about its dependencies, that are listed in materials. But
        you can't get its descendants, though it's possible. This method solves this problem.

        :param pipelines: list of pipelines.
        """
        for pipeline in pipelines:
            descendants = list()

            for candidate in pipelines:
                for material in candidate.predecessors:
                    if material.description == pipeline.data.name:
                        descendants.append(candidate)
            pipeline.descendants = descendants

    def list(self):
        """
        List all available pipelines.

        This method uses ``pipeline_groups`` API method call to list available pipelines.
        It also links them together, so later it's possible to refer to pipeline's descendants.
        :return: array of pipelines
        :rtype: list of yagocd.resources.pipeline.PipelineEntity
        """
        response = self._session.get(
            path='{base_api}/config/pipeline_groups'.format(base_api=self.base_api),
            headers={'Accept': 'application/json'},
        )

        pipelines = list()
        for group in response.json():
            for data in group['pipelines']:
                pipeline = PipelineEntity(
                    session=self._session,
                    data=data,
                    group=group['name']
                )
                pipelines.append(pipeline)

        # link descendants of each pipeline entity
        self.tie_descendants(pipelines)

        return pipelines

    def find(self, name):
        """
        Finds pipeline by it's name.
        :param name: name of required pipeline.
        :return: if found - pipeline :class:`yagocd.resources.PipelineEntity`, otherwise ``None``.
        :rtype: yagocd.resources.PipelineEntity
        """
        for pipeline in self.list():
            if pipeline.data.name == name:
                return pipeline

    def history(self, name, offset=0):
        """
        The pipeline history allows users to list pipeline instances.
        Supports pagination using offset which tells the API how many instances to skip.

        :param name: name of the pipeline.
        :param offset: number of pipeline instances to be skipped.
        :return: an array of pipeline instances :class:`yagocd.resources.pipeline.PipelineInstance`.
        :rtype: list of yagocd.resources.pipeline.PipelineInstance
        """
        response = self._session.get(
            path='{base_api}/pipelines/{name}/history/{offset}'.format(
                base_api=self.base_api,
                name=name,
                offset=offset
            ),
            headers={'Accept': 'application/json'},
        )

        instances = list()
        for instance in response.json().get('pipelines'):
            instances.append(PipelineInstance(session=self._session, data=instance))

        return instances

    def get(self, name, counter):
        """
        Gets pipeline instance object.

        :param name: name of the pipeline.
        :param counter pipeline counter:
        :return: A pipeline instance object :class:`yagocd.resources.pipeline.PipelineInstance`.
        :rtype: yagocd.resources.pipeline.PipelineInstance
        """
        response = self._session.get(
            path='{base_api}/pipelines/{name}/instance/{counter}'.format(
                base_api=self.base_api,
                name=name,
                counter=counter
            ),
            headers={'Accept': 'application/json'},
        )

        return PipelineInstance(session=self._session, data=response.json())

    def status(self, name):
        """
        The pipeline status allows users to check if the pipeline is paused, locked and schedulable.

        :param name: name of the pipeline.
        :return: JSON containing information about pipeline state, wrapped in EasyDict class.
        """
        response = self._session.get(
            path='{base_api}/pipelines/{name}/status'.format(
                base_api=self.base_api,
                name=name,
            ),
            headers={'Accept': 'application/json'},
        )

        return EasyDict(response.json())

    def pause(self, name, cause):
        """
        Pause the specified pipeline.

        :param name: name of the pipeline.
        :param cause: reason for pausing the pipeline.
        """
        self._session.post(
            path='{base_api}/pipelines/{name}/pause'.format(
                base_api=self.base_api,
                name=name,
            ),
            data={'pauseCause': cause},
            headers={'Accept': 'application/json'},
        )

    def unpause(self, name):
        """
        Unpause the specified pipeline.

        :param name: name of the pipeline.
        """
        self._session.post(
            path='{base_api}/pipelines/{name}/unpause'.format(
                base_api=self.base_api,
                name=name,
            ),
            headers={'Accept': 'application/json'},
        )

    def release_lock(self, name):
        """
        Release a lock on a pipeline so that you can start up a new instance
        without having to wait for the earlier instance to finish.

        :param name: name of the pipeline.
        :return: a text confirmation.
        """
        response = self._session.post(
            path='{base_api}/pipelines/{name}/releaseLock'.format(
                base_api=self.base_api,
                name=name,
            ),
            headers={'Accept': 'application/json'},
        )
        return response.text

    def schedule(self, name):
        # TODO: implement me!
        raise NotImplementedError


class PipelineEntity(Base):
    """
    Class for the pipeline entity, which describes pipeline itself.
    Executing ``history`` will return pipeline instances.
    """

    def __init__(self, session, data, group=None, descendants=None):
        super(PipelineEntity, self).__init__(session, data)
        self._group = group
        self._descendants = descendants
        self._pipeline = PipelineManager(session=session)

    @property
    def group(self):
        """
        Name of the group pipeline belongs to.
        :return: group name.
        """
        return self._group

    @property
    def predecessors(self):
        """
        Property for getting predecessors (parents) of current pipeline.
        This property automatically populates from API call

        :return: list of :class:`yagocd.resources.pipeline.PipelineEntity`.
        :rtype: list of yagocd.resources.pipeline.PipelineEntity
        """
        return [material for material in self.data.materials if material.type == 'Pipeline']

    @property
    def descendants(self):
        """
        Property for getting descendants (children) of current pipeline.
        It's calculated by :meth:`yagocd.resources.pipeline.PipelineManager#tie_descendants` method during listing of
        all pipelines.

        :return: list of :class:`yagocd.resources.pipeline.PipelineEntity`.
        :rtype: list of yagocd.resources.pipeline.PipelineEntity
        """
        return self._descendants

    @descendants.setter
    def descendants(self, value):
        self._descendants = value

    def history(self, offset=0):
        return self._pipeline.history(name=self.data.name, offset=offset)

    def status(self):
        return self._pipeline.status(name=self.data.name)

    def pause(self, cause):
        self._pipeline.pause(name=self.data.name, cause=cause)

    def unpause(self):
        self._pipeline.unpause(name=self.data.name)

    def release_lock(self):
        return self._pipeline.release_lock(name=self.data.name)


class PipelineInstance(Base):
    """
    Pipeline instance represents concrete execution of specific pipeline.
    """

    def stages(self):
        stages = list()
        for data in self.data.stages:
            stages.append(StageInstance(session=self._session, data=data, pipeline=self))

        return stages


if __name__ == '__main__':
    pass
