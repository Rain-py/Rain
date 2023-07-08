# Tasks by day

## Friday 30/6

Local Mode

- [x] Don't send the algo.py to the worker.
- [x] Sync training until evaluation.
- [x] Add multiple workers.
- [x] Support PyTorch.
- [x] Test on cifar dataset.

## Saturday 1/7

Local Mode

- [x] Add the local mode to the configuration.
- [x] Coordinator and worker should start automatically in the local mode.
- [x] Add the local provisioner inside the cloud provisioner.
- [x] Async training until evaluation.

## Sunday 2/7

Local Mode

- [x] Add the ML algorithms to the local mode.
- [x] Remove data sending to/from the coordinator.
- [x] Hard coding info in the divider.
- [x] Finish the Docker image of the worker and the algo.
- [x] Add divider proxy.

## Monday 3/7

Cloud Mode

- [x] Start working on the documentation.
- [ ] Circuit breaking.

## Tuesday 4/7

Cloud Mode

- [x] Publish package to pypi.
- [x] Continue working on the documentation.
- [x] Test the onPrem mode with local machines.

## Wednesday 5/7

Cloud Mode

- [x] Test onPrem on the cloud.
- [x] Start working on the cloud mode.

## Thursday 6/7

Cloud Mode

- [x] Fault tolerance in the coordinator.
- [x] Solve hard coding the number of workers in the coordinator.
- [ ] Test scheduling on multiple workers.
- [x] Solve the K-means problem.
- [x] Add stratified partitioning.
- [x] Solve long setup time on the cloud.

## Friday 7/7

- [ ] Test all modes on all examples.
  - MNISt:
    - [x] Local: TF,PT
    - [x] Lazy: TF, PT. Cloud machine.
  - Breast Cancer:
    - [x] Local: NB, LR, KMs
    - [x] Lazy: NB, LR, KMs. Cloud machine.
    - [x] Cloud: TF, NB
  - California Housing:
    - [ ] Cloud: lR
  - CIFAR:
    - [ ] Lazy: TF. Cloud machine.

## Saturday 8/7

- [ ] Continue working on the documentation.

## Sunday 9/7

- [ ] Submit the documentation.

## Monday 10/7

- [ ] Fix the configuration handler. [Easy]
- [ ] Delete rain files after training. [Easy]
- [ ] Stop server in the coordinator doesn't work. Has a TODO. [Easy]
- [ ] Remove port 80(with the apache installation)and 22(with the SSH keys) from the cloud provisioner. [Easy]
- [ ] Add Linting. [Easy]
- [ ] Release Rain on Pypi. [Easy]
- [ ] Fix all logging(types/ add more details in the log, ... ) [Easy]
- [ ] Allow the user to define the used machine in the cloud mode. [Easy]
- [ ] Remove the number of workers from the lazy mode. [Easy]
- [ ] Add a price manager to get the vm specs and choose the right one. [Medium]
- [ ] In the cloud mode, allow communication from the the local machine IP only.
- [ ] Solve read/write disc.[Medium]
- [ ] Use poetry instead of pipenv. [Medium]
- [ ] Add test pipelines.[Medium]
- [ ] Test lazy mode on personal laptops. [Medium]
- [ ] In the cloud mode, stop the VMs without closing them. [Hard]
- [ ] Check all the TODOs.
- [ ] **Submit the code**.

## Future work

- [ ] Add a scheduler.
- [ ] Improve fault tolerance.
- [ ] Add a planar to decide the number of workers/partitions.
- [ ] Add JWT authentication.
