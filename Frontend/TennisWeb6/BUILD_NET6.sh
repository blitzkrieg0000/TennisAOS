#!/bin/bash
#################
#? Settings
#################
export projectName="$(basename $PWD)"

#################
#! Create Web Project with ASP.NET 6 CORE
#################
dotnet new sln &&\

#####################
#! Create SubProjects
#####################
dotnet new classlib -o Business &&\
dotnet new classlib -o Common &&\
dotnet new classlib -o DataAccess &&\
dotnet new classlib -o Dtos  &&\
dotnet new classlib -o Entities  &&\
dotnet new web --name UI &&\

###################
#! Add Dependencies
###################
#dotnet add DataAccess/DataAccess.csproj package Microsoft.EntityFrameworkCore.Proxies &&\    #LazyLoading
#dotnet add DataAccess/DataAccess.csproj package Microsoft.EntityFrameworkCore.SqlServer &&\  #MicrosoftSQL
dotnet add DataAccess/DataAccess.csproj package Npgsql.EntityFrameworkCore.PostgreSQL &&\     #Postgresql
dotnet add DataAccess/DataAccess.csproj package Microsoft.EntityFrameworkCore  &&\
dotnet add DataAccess/DataAccess.csproj package Microsoft.EntityFrameworkCore.Design &&\
dotnet add UI/UI.csproj package Microsoft.EntityFrameworkCore.Design &&\
dotnet add DataAccess/DataAccess.csproj package Microsoft.EntityFrameworkCore &&\
dotnet add Business/Business.csproj package AutoMapper &&\
dotnet add UI/UI.csproj package AutoMapper &&\
dotnet add Business/Business.csproj package FluentValidation &&\
dotnet add Business/Business.csproj package FluentValidation.DependencyInjectionExtensions  &&\
dotnet add Business/Business.csproj package FluentValidation.AspNetCore &&\
dotnet add Business/Business.csproj package Google.Protobuf  &&\
dotnet add Business/Business.csproj package Grpc.AspNetCore  &&\
dotnet add Business/Business.csproj package Grpc.Net.Client  &&\
dotnet add Business/Business.csproj package Grpc.Tools  &&\
dotnet add Business/Business.csproj package Microsoft.AspNetCore.SignalR  &&\

#################
#! Add To Project
#################
dotnet sln $projectName.sln add UI/UI.csproj &&\
dotnet sln $projectName.sln add Business/Business.csproj &&\
dotnet sln $projectName.sln add DataAccess/DataAccess.csproj &&\
dotnet sln $projectName.sln add Dtos/Dtos.csproj &&\
dotnet sln $projectName.sln add Entities/Entities.csproj &&\
dotnet sln $projectName.sln add Common/Common.csproj

#############
#! References
#############
dotnet add DataAccess/DataAccess.csproj reference Entities/Entities.csproj &&\
dotnet add Business/Business.csproj reference DataAccess/DataAccess.csproj &&\
dotnet add Business/Business.csproj reference Dtos/Dtos.csproj &&\
dotnet add Business/Business.csproj reference Common/Common.csproj &&\
dotnet add UI/UI.csproj reference Business/Business.csproj