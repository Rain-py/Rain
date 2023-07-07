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
- [ ] Cloud mode.

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


- [ ] Solve read/write disc.
- [ ] Fix the configuration handler.
- [ ] Submit the code.

# Documentation

Gendy:

| Service Name          | Types | Doc String | GP Doc |
|-----------------------|-------|------------|--------|
| Worker                |  [ ]  |     [ ]    |  [ ]   |
| Deep Learning         |  [x]  |     [x]    |  [ ]   |
| Machine Learning      |  [x]  |     [x]    |  [ ]   |

Nada:

| Service Name          | Types | Doc String | GP Doc |
|-----------------------|-------|------------|--------|
| Worker Ambassador     |  [x]  |     [x]    |  [ ]   |
| Divider Proxy         |  [x]  |     [x]    |  [ ]   |
| Rain                  |  [x]  |     [x]    |  [ ]   |
| Temp File Manager     |  [x]  |     [x]    |  [ ]   |
| Log Service           |  [x]  |     [x]    |  [ ]   |
| Divider               |  [x]  |     [x]    |  [ ]   |

Menna:

| Service Name          | Types | Doc String | GP Doc |
|-----------------------|-------|------------|--------|
| Coordinator           |  [x]  |     [x]    |  [ ]   |
| Provisioner Ambassador|  [x]  |     [x]    |  [x]   |
| Divider Ambassador    |  [x]  |     [x]    |  [x]   |


ُExamples:

tf_mode_data
PT_mode_data
Ml_mode_data
NB_lazy_cloudmachine_breast
LR_lazy_localmacine_breast