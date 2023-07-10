# Mandatory Tasks

- [x] Fix all logging(types/ add more details in the log, ... ).
- [ ] Make the logger class a singleton and add verbose to the config. [Easy]
- [ ] Fix the configuration handler. [Easy]
- [ ] Delete rain files after training. [Easy]
- [ ] Stop server in the coordinator doesn't work. Has a TODO. [Easy]
- [ ] Remove port 80(with the apache installation)and 22(with the SSH keys) from the cloud provisioner. [Easy]
- [ ] Add Linting. [Easy]
- [ ] Release Rain on Pypi. [Easy]
- [x] Allow the user to define the used machine in the cloud mode. [Easy]
- [ ] Remove the number of workers from the lazy mode. [Easy]
- [ ] Documentation that covered installation instructions, usage guides, and detailed API documentation [Easy]
- [ ] Add a price manager to get the vm specs and choose the right one. [Medium]
- [ ] Decide when to call the ambassador and when to inherit from it. [Medium]
- [ ] In the cloud mode, allow communication from the the local machine IP only.
- [ ] Solve read/write disc.[Medium]
- [ ] Use poetry instead of pipenv. [Medium]
- [ ] Add test pipelines.[Medium]
- [ ] Test lazy mode on personal laptops. [Medium]
- [ ] In the cloud mode, stop the VMs without closing them. [Hard]
- [ ] Check all the TODOs.
- [ ] **Submit the code**.

## Future work

- [ ] Improve Fault Tolerance:
  - While Rain has been designed with fault tolerance in mind, there is always room for improvement. As the package is released to the community, new use cases and scenarios may arise that require enhanced fault tolerance mechanisms. Future work could focus on identifying potential failure points and implementing robust fault tolerance strategies to ensure uninterrupted processing and improved system resilience.
- [ ] Scheduler Implementation:
  - To provide more flexibility and optimize resource utilization, a scheduler can be implemented in Rain. Currently, the user needs to manually match the number of workers with the number of partitions. The scheduler can automate this process by dynamically assigning partitions to available workers based on workload and capacity. This feature would improve overall system efficiency and ease the burden on users to manually manage resource allocation.
- [ ] Automatic Planning:
  - To simplify user interaction and optimize system performance, an automatic planning module can be introduced in Rain. This module would analyze the workload and heuristically determine the optimal number of workers and machine types to achieve the best performance. By automating this process, users can focus more on their AI model training tasks and rely on Rain to handle resource planning effectively.
- [ ] Authentication Mechanisms:
  - For companies and organizations, data security and authentication are crucial considerations. Future work could involve adding authentication mechanisms to Rain, ensuring secure communication channels. Implementing technologies like JSON Web Tokens (JWT) in integration with gRPC can provide secure authentication and authorization, allowing companies to protect their data and control access to Rain's resources.
- [ ] Improved Security Measures:
  - As data privacy and security are paramount, enhancing the security measures in Rain is essential. This can involve adding data encryption mechanisms to protect the data during transmission and storage. By incorporating encryption techniques while maintaining performance efficiency, Rain can provide an added layer of security, safeguarding sensitive AI training data.
- [ ] Federated Learning Support: 
  - Extend Rain to support federated learning, enabling the training of AI models on distributed data sources while maintaining data privacy. This would allow organizations and individuals to collaborate on AI model training without sharing sensitive data, promoting privacy-preserving machine learning techniques.
- [ ] Distributed Hyperparameter Optimization: 
  - Implement a module within Rain that allows for distributed hyperparameter optimization. This would enable users to efficiently search for the optimal set of hyperparameters for their AI models, leveraging the distributed computing capabilities of Rain. This feature would save time and resources in the model development process.
- [ ] AutoML Integration: 
  - Integrate automated machine learning (AutoML) capabilities into Rain. This would enable users to automate various stages of the AI model training process, such as data preprocessing, feature engineering, model selection, and hyperparameter tuning. By incorporating AutoML, Rain can streamline and simplify the model development pipeline.
- [ ] Model Versioning and Experiment Tracking: 
  - Introduce a system for model versioning and experiment tracking within Rain. This would enable users to easily manage and track different versions of their AI models, compare performance across experiments, and reproduce previous results. Providing these capabilities would enhance the reproducibility and transparency of AI model training.
- [ ] Visualization and Monitoring: 
  - Develop visualization and monitoring tools within Rain to provide users with real-time insights into the training process. This could include visualizing training metrics, loss curves, model performance, and resource utilization. Offering these visualization and monitoring capabilities would facilitate a better understanding and analysis of AI model training.
- [ ] Integration with Model Serving Platforms: 
  - Integrate Rain with existing model serving platforms to facilitate the deployment and inference of trained AI models. This would provide users with a seamless end-to-end workflow, from model training using Rain to serving the trained models for real-world applications.
- [ ] Reinforcement Learning Support: 
  - Extend Rain to support reinforcement learning algorithms and frameworks. This would enable users to leverage Rain's distributed computing capabilities for training complex reinforcement learning models, opening up possibilities for applications in robotics, game-playing, and autonomous systems.
- [ ] Automated Data Preprocessing: 
  - Integrate automated data preprocessing capabilities into Rain, allowing users to automate common data cleaning, transformation, and feature engineering tasks. This would streamline the data preparation process and reduce the manual effort required before model training.
- [ ] Auto-Scaling and Resource Management: 
  - Implement auto-scaling and dynamic resource management capabilities in Rain. This would allow the system to automatically scale up or down based on workload demands, optimizing resource allocation and minimizing costs.
- [ ] Collaboration and Model Sharing(Improving the lazy mode): 
  - Develop features within Rain that facilitate collaboration and model sharing among users. This could include the ability to share trained models, collaborate on model development, and enable distributed training across multiple organizations or research teams.

