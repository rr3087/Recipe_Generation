library("igraph")
node = read.csv("Nodes.csv", header=FALSE)
colnames(node) = c("id","ingredients")

edge = read.csv("Edges.csv", header=FALSE) # choose an edgelist in .csv file format
colnames(edge) = c("src", "tgt", "weight")
G = graph.data.frame(edge, directed=FALSE) 

eigen = eigen_centrality(G, directed=FALSE, scale=TRUE, weights=NULL, options = arpack_defaults)
btw = betweenness(G, directed=FALSE, weights=NULL, normalized=TRUE)

com = cluster_walktrap(G, weights = E(G)$weight, steps = 4, merges = TRUE, modularity = TRUE, membership = TRUE)
#com=cluster_fast_greedy(G, merges=TRUE, modularity=TRUE, membership=TRUE, weights = E(G)$weight)
#com=cluster_louvain(G, weights = NULL)
membership = as.vector(membership(com))

df = data.frame(eigen$vector, btw, membership)
colnames(df) = c("eigen.centrality","betweenness.centrality","community")
attach(df)
df$id = as.integer(rownames(df))
df = df[order(df$id), ]
df = merge(df, node, by="id")

df1 = df[which(df$community == 1), c("id","ingredients")]
df2 = df[which(df$community == 2), c("id","ingredients")]
write.table(df1, file="nodes_dst.csv", sep=",", row.names=FALSE, col.names=FALSE)
write.table(df2, file="nodes_svy.csv", sep=",", row.names=FALSE, col.names=FALSE)

edge1 = edge[which(edge$src %in% df1$id & edge$tgt %in% df1$id), ]
edge2 = edge[which(edge$src %in% df2$id & edge$tgt %in% df2$id), ]
write.table(edge1, file="edges_dst.csv", sep=",", row.names=FALSE, col.names=FALSE)
write.table(edge2, file="edges_svy.csv", sep=",", row.names=FALSE, col.names=FALSE)
