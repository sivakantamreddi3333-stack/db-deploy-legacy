# Databricks notebook source
# COMMAND ----------

print("Hello from a legacy-deployed notebook (no DABs!)")

# COMMAND ----------

# A very simple sample task: read a table and print a summary
trips = spark.read.table("samples.nyctaxi.trips")
print(f"Total trips in samples.nyctaxi.trips: {trips.count()}")

# COMMAND ----------

display(trips.limit(5))
