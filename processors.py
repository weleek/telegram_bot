# -*- coding: utf-8 -*-
import time
import grpc
from concurrent import futures

import common
from common import Prototype
import network_pb2 as desc
import network_pb2_grpc as ngrpc


class NetworkServicer(ngrpc.NetworkServicer, Prototype):
    def initialize(self):
        self.logger.info(f'{self.__class__.__name__}.initialize call')

    def CmdRequest(self, request, context):
        self.logger.info(f'[{request.type}] - [{request.target}] - [{request.options}]')
        outputs = {}
        if request.type == 'disk' and request.target == 'localhost':
            opt = self.config['target_server'][request.target]
            common.get_disk_space(opt, output=outputs)

        return desc.Response(json=f'{outputs}')


class Server(Prototype):
    server = None

    def initialize(self):
        self.serve()

    def serve(self):
        if self.server is None:
            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

        ngrpc.add_NetworkServicer_to_server(NetworkServicer(), self.server)
        self.server.add_insecure_port(f"[::]:{self.config['server']['port']}")
        self.server.start()
        self.logger.info(f"gRPC server [{self.config['server']['ipaddr']}:{self.config['server']['port']}] start...")

    def run(self):
        try:
            while True:
                time.sleep(86400)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        self.server.stop(0)
        self.logger.info('gRPC server stop...')

